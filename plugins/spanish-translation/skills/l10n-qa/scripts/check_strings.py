#!/usr/bin/env python3
"""Mechanical QA for translated software strings.

Compares a source-language string file with its translation and reports the
problems a script can find with certainty: missing keys, broken placeholders,
lost tags or URLs, text too long for its limit, strings left untranslated,
missing Spanish opening punctuation, and similar. Meaning, register and
terminology are left to the human or model reviewing the report.

Standard library only (Python 3.9+).

Usage:
  check_strings.py en.json es.json
  check_strings.py en.lproj/Localizable.strings es.lproj/Localizable.strings
  check_strings.py values/strings.xml values-es/strings.xml
  check_strings.py messages.po                 (bilingual: msgid -> msgstr)
  check_strings.py app.xliff                   (bilingual: source -> target)
  check_strings.py Localizable.xcstrings --lang es
Options:
  --limit 'button.*=25'   max length for keys matching a glob (repeatable)
  --max-len N             max length for every target string
  --max-ratio R           warn when target is R times longer than source (default 1.4)
  --keep FILE             terms that may stay identical to the source, one per line
  --target-lang es        language of the target (default es; enables ¿ ¡ checks)
  --format md|json        report format (default md)
  --strict                exit 1 on warnings too, not only errors
Exit code: 0 clean, 1 problems found, 2 could not read the input.
"""

import argparse
import fnmatch
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ERROR, WARNING, INFO = "error", "warning", "info"
RANK = {ERROR: 0, WARNING: 1, INFO: 2}


class Entry:
    """One translatable unit. `plural` maps a plural category to its text."""

    def __init__(self, key, text, plural=None, fuzzy=False, line=None):
        self.key = key
        self.text = text
        self.plural = plural or {}
        self.fuzzy = fuzzy
        self.line = line


# ---------------------------------------------------------------- readers


def local(tag):
    return tag.rsplit("}", 1)[-1]


def flatten_xml(elem):
    """Text of an element with child tags kept as simplified markup.

    Inline tags such as <b>, <g id="1"> or <ph id="2"/> become comparable
    tokens, so a lost or added tag shows up as a placeholder mismatch.
    """
    out = [elem.text or ""]
    for child in elem:
        name = local(child.tag)
        ident = child.get("id")
        attr = ' id="%s"' % ident if ident is not None else ""
        if len(child) == 0 and not (child.text or ""):
            out.append("<%s%s/>" % (name, attr))
        else:
            out.append("<%s%s>%s</%s>" % (name, attr, flatten_xml(child), name))
        out.append(child.tail or "")
    return "".join(out)


def read_json(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    entries = {}

    def walk(node, prefix):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, "%s.%s" % (prefix, k) if prefix else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s[%d]" % (prefix, i))
        elif isinstance(node, str):
            entries[prefix] = Entry(prefix, node)

    walk(data, "")
    return entries


STRINGS_PAIR = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;')


def unescape_c(s):
    return re.sub(
        r'\\(u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.)',
        lambda m: {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'"}.get(
            m.group(1), chr(int(m.group(1)[1:], 16)) if m.group(1)[0] in "uU" else m.group(0)
        ),
        s,
    )


def strip_c_comments(text):
    """Remove /* */ and // comments outside of quoted strings."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end - 1
        else:
            out.append(c)
        i += 1
    return "".join(out)


def read_apple_strings(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    entries = {}
    for m in STRINGS_PAIR.finditer(strip_c_comments(text)):
        key = unescape_c(m.group(1))
        entries[key] = Entry(key, unescape_c(m.group(2)))
    return entries


def android_text(s):
    # Android escapes apostrophes and quotes; compare the visible text.
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] == '"':
        s = s[1:-1]
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n").replace("\\@", "@")


def read_android_xml(path):
    root = ET.parse(path).getroot()
    entries = {}
    for el in root:
        name = el.get("name")
        if name is None or el.get("translatable") == "false":
            continue
        kind = local(el.tag)
        if kind == "string":
            entries[name] = Entry(name, android_text(flatten_xml(el)))
        elif kind == "plurals":
            forms = {i.get("quantity"): android_text(flatten_xml(i)) for i in el if local(i.tag) == "item"}
            entries[name] = Entry(name, forms.get("other", ""), plural=forms)
        elif kind == "string-array":
            for idx, item in enumerate(i for i in el if local(i.tag) == "item"):
                key = "%s[%d]" % (name, idx)
                entries[key] = Entry(key, android_text(flatten_xml(item)))
    return entries


def read_po(path):
    """Gettext .po: returns (source_entries, target_entries)."""
    src, tgt = {}, {}
    cur, field, flags, start = {}, None, "", None

    def flush():
        if "msgid" not in cur:
            return
        msgid = cur["msgid"]
        if msgid == "" and "msgctxt" not in cur:  # header entry
            return
        key = (cur["msgctxt"] + "\x04" if "msgctxt" in cur else "") + msgid
        shown = key.replace("\x04", " | ")
        fuzzy = "fuzzy" in flags
        if "msgid_plural" in cur:
            src_forms = {"one": msgid, "other": cur["msgid_plural"]}
            tgt_forms = {}
            for k, v in cur.items():
                if k.startswith("msgstr["):
                    tgt_forms[{"0": "one", "1": "other"}.get(k[7:-1], "form " + k[7:-1])] = v
            src[shown] = Entry(shown, cur["msgid_plural"], plural=src_forms, line=start)
            tgt[shown] = Entry(shown, tgt_forms.get("other", ""), plural=tgt_forms, fuzzy=fuzzy, line=start)
        else:
            src[shown] = Entry(shown, msgid, line=start)
            tgt[shown] = Entry(shown, cur.get("msgstr", ""), fuzzy=fuzzy, line=start)

    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line:
            flush()
            cur, field, flags, start = {}, None, "", None
            continue
        if line.startswith("#,"):
            flags += line[2:]
            continue
        if line.startswith("#"):
            continue
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+"(.*)"$', line)
        if m:
            if m.group(1) in ("msgctxt", "msgid") and any(k.startswith("msgstr") for k in cur):
                flush()
                cur, flags = {}, ""
            field = m.group(1)
            cur[field] = unescape_c(m.group(2))
            start = start or lineno
        elif line.startswith('"') and field:
            cur[field] += unescape_c(line[1:-1])
    flush()
    return src, tgt


def read_xliff(path):
    """XLIFF 1.2 (trans-unit) or 2.x (unit/segment): (source, target)."""
    root = ET.parse(path).getroot()
    src, tgt = {}, {}
    for el in root.iter():
        kind = local(el.tag)
        if kind not in ("trans-unit", "unit"):
            continue
        key = el.get("id") or el.get("resname") or str(len(src))
        segments = [el] if kind == "trans-unit" else [s for s in el if local(s.tag) == "segment"]
        for i, seg in enumerate(segments):
            k = key if len(segments) == 1 else "%s#%d" % (key, i + 1)
            s = next((c for c in seg if local(c.tag) == "source"), None)
            t = next((c for c in seg if local(c.tag) == "target"), None)
            if s is None:
                continue
            src[k] = Entry(k, flatten_xml(s))
            if t is not None:
                state = (t.get("state") or seg.get("state") or "").lower()
                tgt[k] = Entry(k, flatten_xml(t), fuzzy=state in ("needs-review-translation", "needs-translation", "initial"))
    return src, tgt


def read_xcstrings(path, lang):
    """Apple String Catalog: (source, target) for one language."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    base = data.get("sourceLanguage", "en")
    src, tgt = {}, {}

    def unit_value(loc):
        if not isinstance(loc, dict):
            return None, {}
        if "stringUnit" in loc:
            return loc["stringUnit"].get("value", ""), {}
        plural = loc.get("variations", {}).get("plural", {})
        forms = {q: v.get("stringUnit", {}).get("value", "") for q, v in plural.items()}
        return forms.get("other", ""), forms

    for key, item in data.get("strings", {}).items():
        if item.get("shouldTranslate") is False:
            continue
        locs = item.get("localizations", {})
        text, forms = unit_value(locs.get(base))
        if text is None:
            text, forms = key, {}
        src[key] = Entry(key, text, plural=forms)
        if lang in locs:
            t_text, t_forms = unit_value(locs[lang])
            if t_text is not None:
                tgt[key] = Entry(key, t_text, plural=t_forms)
    return src, tgt


MONO = {".json": read_json, ".strings": read_apple_strings, ".xml": read_android_xml}
BILINGUAL = {".po": read_po, ".xliff": read_xliff, ".xlf": read_xliff}


def load(args):
    first = Path(args.source)
    ext = first.suffix.lower()
    if ext == ".xcstrings":
        return read_xcstrings(first, args.target_lang)
    if ext in BILINGUAL:
        if args.target:
            raise ValueError("%s files hold both languages; pass only one file" % ext)
        return BILINGUAL[ext](first)
    if ext not in MONO:
        raise ValueError("unsupported file type %r (json, strings, xml, po, xliff, xlf, xcstrings)" % ext)
    if not args.target:
        raise ValueError("pass both the source file and the translated file")
    return MONO[ext](first), MONO[Path(args.target).suffix.lower()](args.target)


# ---------------------------------------------------------------- tokens

MUSTACHE = re.compile(r"\{\{\s*[^{}]+?\s*\}\}")
ICU_ARG = re.compile(r"\{\s*([A-Za-z_][\w.]*|\d+)\s*(?=[,}])")
DOLLAR = re.compile(r"\$\{[^{}]+\}")
PYNAMED = re.compile(r"%\([\w.]+\)[-+0#]*\d*(?:\.\d+)?[diouxXeEfFgGcrsa]")
PRINTF = re.compile(r"%(?:\d+\$)?[-+0#]*(?:\d+|\*)?(?:\.\d+)?(?:hh|h|ll|l|q|L|z|t|j)?[diouxXeEfFgGaAcspn@]")
TAG = re.compile(r"</?([A-Za-z][\w:-]*)(?:\s[^<>]*?)?(/?)>")
TAG_ID = re.compile(r'\bid="([^"]*)"')
URL = re.compile(r"https?://[^\s<>\"')\]]+|[\w.+-]+@[\w-]+\.[\w.-]+")
CAPITAL_DATE = re.compile(
    r"\b(?:Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo|Enero|Febrero|Marzo|Abril|Mayo|Junio"
    r"|Julio|Agosto|Septiembre|Setiembre|Octubre|Noviembre|Diciembre)\b"
)
NUMBER = re.compile(r"\d[\d.,   ]*\d|\d")


def placeholders(s):
    tokens = []
    rest = s
    for rx in (MUSTACHE, DOLLAR, PYNAMED):
        tokens += [re.sub(r"\s+", "", m) for m in rx.findall(rest)]
        rest = rx.sub(" ", rest)
    rest_no_tags = TAG.sub(" ", rest)
    tokens += ["{%s}" % name for name in ICU_ARG.findall(rest_no_tags)]
    tokens += PRINTF.findall(rest_no_tags.replace("%%", ""))
    return Counter(tokens)


def tags(s):
    out = []
    for m in TAG.finditer(s):
        ident = TAG_ID.search(m.group(0))
        name = m.group(1).lower() + ("#" + ident.group(1) if ident else "")
        out.append(("</%s>" if m.group(0).startswith("</") else "<%s/>" if m.group(2) else "<%s>") % name)
    return Counter(out)


def numbers(s):
    stripped = TAG.sub(" ", PRINTF.sub(" ", s))
    return Counter(re.sub(r"\D", "", n) for n in NUMBER.findall(stripped))


def diff(a, b):
    missing = sorted((a - b).elements())
    extra = sorted((b - a).elements())
    return missing, extra


# ---------------------------------------------------------------- checks


def check_pair(key, s, t, opts, out):
    def add(level, kind, detail):
        out.append({"level": level, "key": key, "check": kind, "detail": detail, "source": s, "target": t})

    if not t.strip():
        add(ERROR, "empty", "translation is empty")
        return

    m, e = diff(placeholders(s), placeholders(t))
    if m or e:
        add(ERROR, "placeholder", "missing %s; extra %s" % (m or "none", e or "none"))

    m, e = diff(tags(s), tags(t))
    if m or e:
        add(ERROR, "markup", "tags differ: missing %s; extra %s" % (m or "none", e or "none"))

    m, e = diff(Counter(URL.findall(s)), Counter(URL.findall(t)))
    if m or e:
        add(ERROR, "url", "links or emails differ: missing %s; extra %s" % (m or "none", e or "none"))

    if s.count("\n") != t.count("\n"):
        add(WARNING, "line-breaks", "source has %d line breaks, translation has %d" % (s.count("\n"), t.count("\n")))

    m, e = diff(numbers(s), numbers(t))
    if m or e:
        add(WARNING, "numbers", "numbers differ: missing %s; extra %s" % (m or "none", e or "none"))

    limit = opts.max_len
    for pattern, n in opts.limits:
        if fnmatch.fnmatchcase(key, pattern):
            limit = n
    visible = len(TAG.sub("", t))
    if limit and visible > limit:
        add(ERROR, "length", "%d characters; limit is %d" % (visible, limit))
    elif len(s) >= 12 and visible > len(TAG.sub("", s)) * opts.max_ratio:
        add(WARNING, "length", "%.1fx the source length; check it fits the screen" % (visible / max(1, len(TAG.sub("", s)))))

    if s.strip() == t.strip() and re.search(r"[A-Za-z]{4,}", s):
        words = set(re.findall(r"[A-Za-z][\w'-]*", s))
        if not words <= opts.keep:
            add(WARNING, "untranslated", "identical to the source")

    if s[:1].isspace() != t[:1].isspace() or s[-1:].isspace() != t[-1:].isspace():
        add(WARNING, "whitespace", "leading or trailing spaces differ from the source")

    if opts.target_lang.startswith("es"):
        visible_text = TAG.sub(" ", t)
        if "?" in visible_text and "¿" not in visible_text:
            add(WARNING, "punctuation", "question without opening ¿")
        if "!" in visible_text and "¡" not in visible_text:
            add(WARNING, "punctuation", "exclamation without opening ¡")
        for m in CAPITAL_DATE.finditer(visible_text):
            before = visible_text[: m.start()].rstrip()
            if before and before[-1] not in ".:¿¡!?\n\"«":
                add(WARNING, "capitalization", "%r: days and months are lowercase in Spanish mid-sentence" % m.group(0))

    if "  " in t and "  " not in s:
        add(INFO, "whitespace", "double space in the translation")


def run(source, target, opts):
    findings = []
    for key, s in source.items():
        t = target.get(key)
        if t is None:
            findings.append({"level": ERROR, "key": key, "check": "missing", "detail": "no translation for this key", "source": s.text, "target": ""})
            continue
        if t.fuzzy:
            findings.append({"level": WARNING, "key": key, "check": "needs-review", "detail": "marked fuzzy or needs review in the file", "source": s.text, "target": t.text})
        if s.plural or t.plural:
            check_pair(key, s.text, t.text, opts, findings)
            if t.plural and "other" not in t.plural:
                findings.append({"level": ERROR, "key": key, "check": "plural", "detail": "Spanish plural needs at least 'one' and 'other' forms; has %s" % sorted(t.plural), "source": s.text, "target": t.text})
            elif t.plural and "one" not in t.plural:
                findings.append({"level": WARNING, "key": key, "check": "plural", "detail": "no 'one' form; Spanish uses one and other", "source": s.text, "target": t.text})
            for q, txt in t.plural.items():
                if q != "other":
                    check_pair("%s (%s)" % (key, q), s.plural.get(q, s.text), txt, opts, findings)
        else:
            check_pair(key, s.text, t.text, opts, findings)
        if re.search(r"\b(?:plural|selectordinal)\b", s.text) and not re.search(r"\bother\s*\{", t.text):
            findings.append({"level": ERROR, "key": key, "check": "plural", "detail": "ICU plural without an 'other' branch", "source": s.text, "target": t.text})
    for key in target:
        if key not in source:
            findings.append({"level": WARNING, "key": key, "check": "extra", "detail": "key is not in the source file", "source": "", "target": target[key].text})
    order = {k: i for i, k in enumerate(source)}
    findings.sort(key=lambda f: (RANK[f["level"]], order.get(f["key"].split(" (")[0], len(order))))
    return findings


# ---------------------------------------------------------------- report


def cell(s, n=70):
    s = s.replace("\n", "⏎").replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def report_md(findings, total):
    counts = Counter(f["level"] for f in findings)
    lines = [
        "# Localization QA",
        "",
        "%d strings checked: %d errors, %d warnings, %d notes." % (total, counts[ERROR], counts[WARNING], counts[INFO]),
        "",
    ]
    if not findings:
        lines.append("No mechanical problems found. Meaning, register and terminology still need a human or model review.")
        return "\n".join(lines)
    lines += ["| Level | Key | Check | Problem | Source | Translation |", "|---|---|---|---|---|---|"]
    for f in findings:
        lines.append("| %s | `%s` | %s | %s | %s | %s |" % (f["level"], cell(f["key"], 40), f["check"], cell(f["detail"], 80), cell(f["source"]), cell(f["target"])))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source")
    ap.add_argument("target", nargs="?")
    ap.add_argument("--limit", action="append", default=[], metavar="GLOB=N")
    ap.add_argument("--max-len", type=int)
    ap.add_argument("--max-ratio", type=float, default=1.4)
    ap.add_argument("--keep", metavar="FILE")
    ap.add_argument("--target-lang", "--lang", default="es")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("--strict", action="store_true")
    opts = ap.parse_args(argv)

    try:
        opts.limits = [(g, int(n)) for g, n in (x.rsplit("=", 1) for x in opts.limit)]
        keep = Path(opts.keep).read_text(encoding="utf-8").split("\n") if opts.keep else []
        opts.keep = {w.strip() for line in keep for w in re.findall(r"[A-Za-z][\w'-]*", line)}
        source, target = load(opts)
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError, UnicodeDecodeError) as err:
        print("Could not read the input: %s" % err, file=sys.stderr)
        return 2

    findings = run(source, target, opts)
    if opts.format == "json":
        print(json.dumps({"checked": len(source), "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(report_md(findings, len(source)))
    failing = [f for f in findings if f["level"] == ERROR or (opts.strict and f["level"] == WARNING)]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())

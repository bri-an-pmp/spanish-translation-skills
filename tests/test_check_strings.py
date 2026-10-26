"""Tests for the l10n-qa checker, run against the files in examples/."""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(ROOT / "plugins/spanish-translation/skills/l10n-qa/scripts"))
import check_strings  # noqa: E402


def check(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = check_strings.main([*map(str, args), "--format", "json"])
    data = json.loads(out.getvalue()) if code != 2 else None
    found = {(f["key"], f["check"]) for f in data["findings"]} if data else set()
    return code, found


class Json(unittest.TestCase):
    def setUp(self):
        self.code, self.found = check(EXAMPLES / "json/en.json", EXAMPLES / "json/es.json", "--limit", "button.*=25")

    def test_exit_code(self):
        self.assertEqual(self.code, 1)

    def test_planted_bugs(self):
        expected = {
            ("button.invite", "length"),
            ("button.delete", "untranslated"),
            ("confirm.delete_body", "placeholder"),
            ("confirm.delete_body", "markup"),
            ("error.upload", "placeholder"),
            ("help.docs", "url"),
            ("help.webhook", "numbers"),
            ("toast.invite_sent", "punctuation"),
            ("items", "plural"),
            ("settings.title", "missing"),
            ("extra_key", "extra"),
        }
        self.assertLessEqual(expected, self.found)

    def test_correct_strings_pass(self):
        flagged = {key for key, _ in self.found}
        for key in ("button.save", "confirm.delete_title", "error.rate_limit"):
            self.assertNotIn(key, flagged)


class OtherFormats(unittest.TestCase):
    def test_po(self):
        code, found = check(EXAMPLES / "po/es.po")
        self.assertEqual(code, 1)
        self.assertLessEqual(
            {("You have %d new message", "placeholder"), ("You have %d new message", "needs-review"),
             ("menu | Open", "empty"), ("Are you sure?", "punctuation")},
            found,
        )
        self.assertNotIn("Hello, %s!", {key for key, _ in found})

    def test_android(self):
        code, found = check(EXAMPLES / "android/values/strings.xml", EXAMPLES / "android/values-es/strings.xml")
        self.assertIn(("greeting", "markup"), found)
        self.assertNotIn("app_name", {key for key, _ in found})  # translatable="false"

    def test_xliff(self):
        code, found = check(EXAMPLES / "xliff/app.xliff")
        self.assertLessEqual({("cta", "markup"), ("meeting", "needs-review"), ("meeting", "capitalization")}, found)


class Tokens(unittest.TestCase):
    def test_placeholder_kinds(self):
        tokens = check_strings.placeholders("Hi {{ name }}, %1$s %d %@ ${x} %(user)s {count, plural, one {# a} other {# b}} 100%%")
        self.assertEqual(
            set(tokens),
            {"{{name}}", "%1$s", "%d", "%@", "${x}", "%(user)s", "{count}"},
        )

    def test_percent_sign_is_not_a_placeholder(self):
        self.assertEqual(sum(check_strings.placeholders("50% de descuento, 100 % seguro").values()), 0)

    def test_number_separators_ignored(self):
        self.assertEqual(check_strings.numbers("1,500.75"), check_strings.numbers("1.500,75"))


class Errors(unittest.TestCase):
    def test_unreadable_input(self):
        code, _ = check(EXAMPLES / "missing.json", EXAMPLES / "json/es.json")
        self.assertEqual(code, 2)

    def test_bilingual_file_with_two_paths(self):
        code, _ = check(EXAMPLES / "po/es.po", EXAMPLES / "po/es.po")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

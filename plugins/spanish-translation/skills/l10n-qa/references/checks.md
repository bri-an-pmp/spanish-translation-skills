# What `check_strings.py` checks

| Check | Level | What it catches | Expect false positives when… |
|---|---|---|---|
| `missing` | error | A source key with no translation | The key is intentionally untranslatable but not marked (`translatable="false"`, `shouldTranslate: false`) |
| `empty` | error | Translation is blank | Never — an empty string shows nothing on screen |
| `placeholder` | error | `{{x}}`, `{x}`, `${x}`, `%s`, `%1$s`, `%@`, `%(name)s`, `%lld`, ICU argument names: lost, added, renamed, or changed type (`%d` → `%s`) | A target legitimately repeats a placeholder (rare; confirm with the developer) |
| `markup` | error | HTML tags (`<b>`, `<a>`) and XLIFF inline tags (`<g id="1">`, `<x id="2"/>`) lost or added | The translation deliberately drops emphasis — still confirm |
| `url` | error | Links and email addresses changed | The target links to a localized page on purpose (`/es/`) — then it's fine, say so |
| `length` | error / warning | Over a `--limit` or `--max-len` (error); more than `--max-ratio` × the source length for strings of 12+ characters (warning) | Long text in a scrolling view — the ratio warning is a prompt to check, not a defect |
| `plural` | error / warning | ICU plural without `other`; platform plural without `other` or `one` | — |
| `needs-review` | warning | `.po` entries marked `fuzzy`; XLIFF `needs-review-translation`, `needs-translation`, `initial` | — |
| `untranslated` | warning | Target identical to the source and contains a real word | Brand names, `OK`, `API`, `Email` in some products — add them to `--keep` |
| `numbers` | warning | Digits changed (`5` → `50`), ignoring separators so `1,000.5` = `1.000,5` | Numbers written out as words in one language |
| `line-breaks` | warning | Different number of `\n` | Deliberate reflow for a narrower label |
| `whitespace` | warning / note | Leading or trailing spaces differ (often a concatenated string); double spaces | — |
| `punctuation` | warning | `?` without `¿`, `!` without `¡` (Spanish targets) | The opening mark is in a separate, concatenated string |
| `capitalization` | warning | A day or month capitalized mid-sentence (`el Lunes`) | Proper names such as `Viernes Santo` |
| `extra` | warning | Keys in the translation that the source no longer has (stale strings) | — |

Formats read: JSON (nested keys become `a.b.c`), Apple `.strings` (UTF-8 or UTF-16) and `.xcstrings` (needs `--lang`), Android `strings.xml` (`<string>`, `<plurals>`, `<string-array>`), gettext `.po` (with `msgctxt` and plurals), XLIFF 1.2 and 2.x.

## Spanish locale notes

- **Plurals.** Spanish uses `one` and `other`. Newer CLDR data also defines `many` for Spanish (used with large round numbers, as in *un millón de usuarios*), and some tools ask for it. Treat a missing `many` as a note, not an error.
- **`one` is not only 1.** With ICU, `one` can match `1` and also decimals in some locales; use `=1 {…}` when the text must mean exactly one.
- **Decimal and thousands separators vary by country.** Mexico and much of Central America use a decimal point (`1,500.75`), while Spain, Argentina, Colombia, Chile and Costa Rica use a decimal comma (`1.500,75`). Neutral Latin American text should get its number format from the app's locale settings, not hard-coded in the string. Flag hard-coded formatted numbers.
- **Percent.** RAE recommends a space before `%` (`50 %`); many products keep `50%`. Pick one per file.
- **Lowercase**: days, months, languages, nationalities (`lunes`, `octubre`, `español`).
- **Dates.** `DD/MM/AAAA` order in most of the Spanish-speaking world; never assume `MM/DD`. Prefer locale date formatting over hard-coded dates.
- **Opening punctuation** goes where the question or exclamation starts, which may be mid-sentence: `Si no lo encuentra, ¿ya revisó la carpeta de spam?`

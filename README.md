<img src="plugins/spanish-translation/.claude-plugin/icon.png" alt="" width="96" align="right">

# Spanish Translation Skills for Claude

Three skills that make Claude work like a careful English ↔ Spanish translator: it translates with a translator's report, checks Spanish against the RAE, and catches the localization bugs that break apps.

Built by a working translator ([Notary Confi](https://notaryconfi.com)) for translators who are comfortable with technology. *[Leer en español ↓](#en-español)*

| Skill | What it does | Ask it, for example |
|---|---|---|
| **translator-en-es** | Translates EN ↔ ES (neutral Latin American by default) and returns a full translator's report: register and audience analysis, the translation, a glossary, and numbered notes on every judgment call. Has reference guides for legal and notarial, SaaS and UI, business, and community-arts texts. | "Certified English translation of this Mexican power of attorney" |
| **rae-spanish** | Checks spelling, grammar and usage against live RAE sources (DLE, DPD) and cites them. It only says "the RAE says" after checking. | "¿Se dice *pienso de que* o *pienso que*?" |
| **l10n-qa** | QA for translated app strings. A script catches broken placeholders, lost tags, changed links and numbers, text over a character limit, and missing keys. Claude then reviews register, terminology and grammar around placeholders. | "QA es.json against en.json, buttons max 25 characters" |

## Install

**Claude Code.** Run these two commands in a Claude Code session:

```
/plugin marketplace add bri-an-pmp/spanish-translation-skills
/plugin install spanish-translation@spanish-translation-skills
```

The skills load on their own when a request needs them. You can also call one by name: `/spanish-translation:l10n-qa`.

**Claude.ai (web and desktop).** Download this repository (**Code → Download ZIP**). Then zip one skill's folder from `plugins/spanish-translation/skills/`; the zip must contain the folder itself, for example `l10n-qa/SKILL.md`. Upload it under **Customize → Skills** ([claude.ai/customize/skills](https://claude.ai/customize/skills)). Code execution must be turned on for the checker to run.

## The checker on its own

`l10n-qa` includes a standalone script. It needs only Python 3.9+, with no installs, so you can run it without Claude or add it to a build pipeline:

```bash
python3 plugins/spanish-translation/skills/l10n-qa/scripts/check_strings.py en.json es.json --limit 'button.*=25'
```

It reads JSON, Apple `.strings` and `.xcstrings`, Android `strings.xml`, gettext `.po`, and XLIFF 1.2/2.x. Run against the sample files in [`examples/`](examples/), it reports:

```
13 strings checked: 7 errors, 5 warnings, 0 notes.

| Level | Key                 | Check       | Problem                                       |
|-------|---------------------|-------------|-----------------------------------------------|
| error | button.invite       | length      | 32 characters; limit is 25                    |
| error | confirm.delete_body | placeholder | missing ['{{count}}']; extra ['{{cuenta}}']   |
| error | confirm.delete_body | markup      | tags differ: missing ['</b>', '<b>']          |
| error | error.upload        | placeholder | missing ['%2$d']; extra ['%2$s']              |
| error | items               | plural      | ICU plural without an 'other' branch          |
| warn  | help.webhook        | numbers     | numbers differ: missing ['5']; extra ['50']   |
| warn  | toast.invite_sent   | punctuation | exclamation without opening ¡                 |
```

The exit code is 1 when there are errors, so a CI job can block a release on broken strings. Every check, and when to expect false alarms, is listed in [`checks.md`](plugins/spanish-translation/skills/l10n-qa/references/checks.md).

## How it's tested

- **Checker:** `python3 -m unittest discover -s tests` runs the tests on every push ([workflow](.github/workflows/test.yml)). The sample files contain deliberate mistakes, and each one must be caught.
- **Skills:** [`plugins/spanish-translation/evals/`](plugins/spanish-translation/evals/) holds six Claude Code eval cases: a notarial power of attorney, SaaS UI strings, a B2B email, a string-file QA with six planted bugs, an RAE question, and a French question that should *not* trigger the skills. Each case is graded by rules (placeholders kept, the right skill used) and by an AI judge with a written rubric, and it runs both with and without the plugin to show the difference. To run them: `claude plugin eval plugins/spanish-translation`. This uses your Claude plan.

### Results (October 26, 2026)

Each case ran 3 times with the skills and 3 times with plain Claude (Claude Code 2.1.310, graded by Sonnet). "Passed" means every check in the case passed; "score" is the share of checks passed.

| Case | With the skills | Plain Claude |
|---|---|---|
| RAE question: *¿pienso de que?* | **3/3 passed** | 0/3 passed |
| Mexican power of attorney → certified English | **3/3 passed** | 1/3 passed (score 83%) |
| SaaS UI strings, 25-character buttons | **3/3 passed** | 2/3 passed (score 93%) |
| B2B renewal email → Colombian client | 2/3 passed (score 92%) | 2/3 passed (score 92%) |
| QA of a string file with 6 planted bugs | 3/3 passed | 3/3 passed |
| French question (skills must stay quiet) | 3/3 passed | 3/3 passed |

What this shows:
- The skills help most where a fact has to be checked (the RAE question) and with specialized conventions (notarial terms of art, developer terminology).
- For an everyday business email, plain Claude is already about as good.
- The 6-bug string file was small enough that plain Claude caught everything too. The script matters more on large files, where reading every line by eye misses things.
- An early version of the test graded each translation with one long all-or-nothing rubric and failed translations that were actually good. Splitting the rubric into one question per requirement fixed that.

## Limits

- These skills produce a draft and a review. They don't replace a certified translator's signature, and the translator's certification block leaves the name blank on purpose.
- The checker finds mechanical problems with certainty, but it can't judge meaning. A string that passes can still be wrong, which is why the skill adds a human-style review on top.
- `rae-spanish` needs web access to verify rules. Without it, the skill marks its findings as unverified.

## License

[MIT](LICENSE). Contributions and corrections are welcome, especially from other translators. Open an issue or a pull request.

---

## En español

Tres *skills* que hacen que Claude trabaje como un traductor cuidadoso de inglés ⇄ español: traduce con un informe de traducción, revisa el español con las fuentes de la RAE y detecta los errores de localización que rompen una aplicación.

Las creó un traductor en ejercicio ([Notary Confi](https://notaryconfi.com)) para traductores que se manejan bien con la tecnología.

| Skill | Qué hace | Puede pedirle, por ejemplo |
|---|---|---|
| **translator-en-es** | Traduce EN ⇄ ES (español latinoamericano neutro por defecto) y entrega un informe completo: análisis de registro y público, la traducción, un glosario y notas numeradas sobre cada decisión. Incluye guías para textos jurídicos y notariales, SaaS e interfaces, empresariales y de artes comunitarias. | "Traducción certificada al inglés de este poder notarial mexicano" |
| **rae-spanish** | Revisa ortografía, gramática y uso con fuentes vigentes de la RAE (DLE, DPD) y las cita. Solo afirma "la RAE dice" después de comprobarlo. | "¿Se dice *pienso de que* o *pienso que*?" |
| **l10n-qa** | Control de calidad de *strings* traducidos. Un *script* detecta variables rotas, etiquetas perdidas, enlaces y números alterados, textos que superan el límite de caracteres y claves faltantes. Después, Claude revisa el registro, la terminología y la concordancia alrededor de las variables. | "Revise es.json contra en.json; los botones tienen un máximo de 25 caracteres" |

### Instalación

**Claude Code.** Ejecute estos dos comandos en una sesión de Claude Code:

```
/plugin marketplace add bri-an-pmp/spanish-translation-skills
/plugin install spanish-translation@spanish-translation-skills
```

Las *skills* se activan solas cuando una solicitud las necesita. También puede llamar una por su nombre: `/spanish-translation:l10n-qa`.

**Claude.ai (web y escritorio).** Descargue este repositorio (**Code → Download ZIP**). Luego comprima en un ZIP la carpeta de una *skill* que está en `plugins/spanish-translation/skills/`; el ZIP debe contener la carpeta misma, por ejemplo `l10n-qa/SKILL.md`. Súbala en **Customize → Skills** ([claude.ai/customize/skills](https://claude.ai/customize/skills)). Para usar el verificador, la ejecución de código debe estar activada.

### El verificador por separado

`l10n-qa` incluye un *script* independiente. Solo necesita Python 3.9 o posterior, sin instalar nada más, así que puede usarlo sin Claude o integrarlo en un proceso de compilación:

```bash
python3 plugins/spanish-translation/skills/l10n-qa/scripts/check_strings.py en.json es.json --limit 'button.*=25'
```

Lee JSON, `.strings` y `.xcstrings` de Apple, `strings.xml` de Android, `.po` de gettext y XLIFF 1.2/2.x. Si encuentra errores, termina con el código 1, para que un proceso de integración continua pueda detener una versión con *strings* rotos. En [`checks.md`](plugins/spanish-translation/skills/l10n-qa/references/checks.md) se explica cada verificación y cuándo puede dar falsas alarmas.

### Cómo se prueba

- **Verificador:** `python3 -m unittest discover -s tests` ejecuta las pruebas con cada cambio. Los archivos de ejemplo contienen errores a propósito, y cada uno debe detectarse.
- **Skills:** [`plugins/spanish-translation/evals/`](plugins/spanish-translation/evals/) contiene seis casos de evaluación: un poder notarial, *strings* de una interfaz SaaS, un correo empresarial, una revisión de un archivo de *strings* con seis errores sembrados, una consulta sobre la RAE y una pregunta sobre francés que *no* debe activar las *skills*. Cada caso se califica con reglas (por ejemplo, que se conserven las variables) y con un juez de IA que sigue una rúbrica escrita. Además, se ejecuta con y sin el *plugin* para medir la diferencia. Para ejecutarlos: `claude plugin eval plugins/spanish-translation`. Esto consume el uso de su plan de Claude.

### Resultados (26 de octubre de 2026)

Cada caso se ejecutó 3 veces con las *skills* y 3 veces con Claude sin ellas; la calificación la hizo Sonnet.

| Caso | Con las skills | Claude sin skills |
|---|---|---|
| Consulta RAE: *¿pienso de que?* | **3/3 aprobados** | 0/3 aprobados |
| Poder notarial mexicano → traducción certificada al inglés | **3/3 aprobados** | 1/3 aprobados (83 %) |
| *Strings* de una interfaz SaaS, botones de 25 caracteres | **3/3 aprobados** | 2/3 aprobados (93 %) |
| Correo de renovación para un cliente colombiano | 2/3 aprobados (92 %) | 2/3 aprobados (92 %) |
| Revisión de un archivo de *strings* con 6 errores sembrados | 3/3 aprobados | 3/3 aprobados |
| Pregunta sobre francés (las *skills* no deben activarse) | 3/3 aprobados | 3/3 aprobados |

Las *skills* ayudan más cuando hay que comprobar un dato (la consulta a la RAE) y con convenciones especializadas (términos notariales, terminología para desarrolladores). En un correo empresarial común, Claude sin *skills* ya rinde casi igual.

### Límites

- Estas *skills* producen un borrador y una revisión. No sustituyen la firma de un traductor certificado; el bloque de certificación deja el nombre en blanco a propósito.
- El verificador encuentra con certeza los problemas mecánicos, pero no puede juzgar el sentido. Un *string* que pasa la verificación puede seguir estando mal; por eso la *skill* agrega una revisión como la de una persona.
- `rae-spanish` necesita acceso a internet para comprobar las normas. Sin él, marca sus observaciones como no verificadas.

### Licencia

[MIT](LICENSE). Las contribuciones y correcciones son bienvenidas, sobre todo de otros traductores. Abra un *issue* o un *pull request*.

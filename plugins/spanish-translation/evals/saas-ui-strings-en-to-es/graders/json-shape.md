---
type: llm
---

PASS if the reply contains the translated JSON with exactly the same 13 keys as the source, unchanged, and every placeholder ({{count}}, {{seconds}}, {{email}}) preserved byte-for-byte. FAIL if any key is renamed, missing or added, or any placeholder is altered.

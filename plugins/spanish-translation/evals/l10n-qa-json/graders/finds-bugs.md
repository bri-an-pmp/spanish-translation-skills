---
type: llm
---

PASS only if the reply flags ALL of these:
1. `{{cuenta}}` is a renamed placeholder; it must stay `{{count}}`.
2. The `<b>` tags around `{{workspace}}` were lost.
3. "Invitar a un compañero de equipo" is over the 25-character button limit, with a shorter suggestion.
4. "5 seconds" became "50 segundos".
5. The opening "¡" is missing in the invite toast.
6. "Te damos la bienvenida" uses tú while the rest of the file uses usted (formal voice requested).

FAIL if any of the six is missed, or if the reply suggests translating or renaming a placeholder.

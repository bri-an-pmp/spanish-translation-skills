---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Can you QA our Spanish strings before release? Buttons must fit 25 characters. B2B app, formal voice.

en.json:
```json
{
  "button.invite": "Invite teammate",
  "confirm.delete_body": "This will permanently remove {{count}} integrations from <b>{{workspace}}</b>.",
  "error.rate_limit": "You've hit the rate limit. Try again in {seconds} seconds.",
  "toast.welcome": "Welcome back, {name}.",
  "toast.invite_sent": "Invite sent to {email}!",
  "help.webhook": "Your endpoint must respond within 5 seconds."
}
```

es.json:
```json
{
  "button.invite": "Invitar a un compañero de equipo",
  "confirm.delete_body": "Esto eliminará permanentemente {{cuenta}} integraciones de {{workspace}}.",
  "error.rate_limit": "Alcanzó el límite de uso. Vuelva a intentarlo en {seconds} segundos.",
  "toast.welcome": "Te damos la bienvenida de nuevo, {name}.",
  "toast.invite_sent": "Invitación enviada a {email}!",
  "help.webhook": "Su endpoint debe responder en un máximo de 50 segundos."
}
```

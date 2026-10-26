---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Localize these UI strings for our B2B SaaS product to neutral Latin American Spanish. The product is a developer platform for managing API integrations — clinical, formal brand voice (think Stripe, not Mailchimp). Audience is engineering managers and senior devs. Preserve all placeholders. Button labels and confirmation titles should fit in roughly the same character budget as English (max 25 chars for buttons).

```json
{
  "button.save": "Save changes",
  "button.delete": "Delete",
  "button.cancel": "Cancel",
  "button.invite": "Invite teammate",
  "confirm.delete.title": "Delete {{count}} integrations?",
  "confirm.delete.body": "This will permanently remove {{count}} integrations from your workspace. This action cannot be undone.",
  "error.rate_limit": "You've hit the rate limit. Try again in {{seconds}} seconds.",
  "empty_state.title": "No integrations yet",
  "empty_state.body": "Connect your first API to start syncing data across your stack.",
  "toast.invite_sent": "Invite sent to {{email}}",
  "webhook.help": "Your webhook endpoint must return a 2xx status code within 5 seconds.",
  "settings.api_key.label": "API key",
  "settings.api_key.help": "Use this key in the Authorization header of your requests."
}
```

Return the translated JSON in the same shape, and include the translator's report.

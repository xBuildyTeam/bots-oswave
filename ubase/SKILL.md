---
name: ubase-packet-builder
description: Build a uBase packet (format wave.ubase/2), a zip that adds one feature to a Base44 app. Use when a user or bot asks to make, package or submit a uBase packet. Includes the file layout, meta.json fields, the install prompt template, the rules, and the checker every packet must pass.
version: 0.2.0
---

# How to build a uBase packet (wave.ubase/2)

A uBase packet is a `.ubase` file: a zip that adds ONE feature to a Base44 app (a component, a backend
function, entity schemas, or all three). People install it from https://ubase.tech with the uBase Installer;
the Base44 builder AI reads `prompt.md` and puts the files in place.

Guide home: https://bots.oswave.io/ubase/ (this file, `meta.schema.json`, `check_packet.py`, an example packet).

## 1. Layout

All files at the zip ROOT (no wrapping folder):

```
meta.json            required: what the packet is (section 2)
prompt.md            required: the install steps for the Base44 builder AI (section 3)
README.md            required: for people (what it does, setup, requirements)
INSTALL.md, LICENSE  optional
components/*.jsx     React components (default export, Tailwind classes, no outside CSS)
functions/*.ts       Base44 backend functions (Deno, one Deno.serve handler per file)
entities/*.json      entity schemas: {"name": "...", "type": "object", "properties": {...}}
assets/*             optional, small: png, jpg/jpeg, svg, html, json, md, txt, css
previews/*           optional screenshots for the store page
```

Keep it small: under 45,000 bytes zipped. One feature per packet. Nothing else goes in the zip.

## 2. meta.json

```json
{
  "format": "wave.ubase/2",
  "target": "base44",
  "name": "digital-clock",
  "title": "Digital Clock",
  "version": "1.0.0",
  "description": "One or two plain sentences: what it adds and where.",
  "category": "UI Components",
  "tags": ["clock", "time"],
  "price": 0,
  "author_name": "Your bot or your name",
  "author_wallet": "0x0000000000000000000000000000000000000000",
  "placeholders": [
    { "key": "TIMEZONE", "label": "Time zone", "description": "IANA name, e.g. America/Los_Angeles", "default": "UTC" }
  ],
  "placement": { "prompt_user": true, "component": "DigitalClock", "suggested_pages": ["Dashboard"] },
  "permissions": {
    "entities": [], "functions": [], "secrets": [], "connectors": [],
    "admin_access": false, "outside_hosts": []
  },
  "files": {
    "components/DigitalClock.jsx": { "sha256": "<hex sha256 of the file bytes>" }
  }
}
```

Rules:
* `author_wallet`: the full 0x address (40 hex characters) of the wallet that will mint the packet card. Optional
  for people; leave the field out rather than using a placeholder.
* `name`: lowercase-with-dashes. `version`: x.y.z (bump it for every change).
* `category`: one of UI Components, Integrations, Utilities, Data, Messaging, Payments, Security, AI, Dev.
* `files`: EVERY file under components/, functions/, entities/ and assets/, each with its sha256.
* `permissions`: tell the truth. List every entity the packet creates, every function it adds, every secret
  name it needs (e.g. `STRIPE_SECRET_KEY`), connectors, outside hosts it calls (e.g. `api.stripe.com`), and
  set `admin_access: true` if any function uses `asServiceRole`. Installers see this before installing.
* `placeholders`: every `{{TOKEN}}` used in code must be declared here, and every declared one used. Token
  names are UPPER_SNAKE_CASE (`{{BRAND_COLOR}}`, never `{{brandColor}}`).

## 3. prompt.md template

```markdown
# <Title>: Builder AI install prompt

You are installing the <Title> packet into a Base44 app.

1. Ask the user: <one line per placeholder, with the default>
2. Create these entities exactly as in entities/: <list, or "none">
3. Add these backend functions exactly as written: <list, or "none">
   Secrets to set in the app's settings: <list, or "none">
4. Add <Component>.jsx to src/components/ and replace {{TOKENS}} with the answers.
5. Place it on the page the user picks: `<Component />` (props: <list>)
6. Tell the user: "<one sentence on how to use it>"

Do not change any other file in the app.
```

Replace every `<...>` blank with real text. The checker refuses a `prompt.md` that still has template blanks,
that is very short, or that tells the installer to use `eval`/`new Function` (in words or in a code example).

## 4. Code rules (the checker enforces these)

Blocked (the packet is refused):
* Any real secret or key in any file, including README and prompt.md. Webhook URLs are secrets too (Slack,
  Discord, Teams, Telegram bot URLs), and so are keys in a link (`?api_key=…`). Use `Deno.env.get("NAME")`
  and list NAME in permissions.secrets. If a user hands you a key or webhook, never copy it into the packet.
* `eval(`, `new Function(`, string-built code, minified or obfuscated code. If a user asks for eval, write a
  small parser instead. (Mentioning eval in a comment is fine.)
* Loading outside scripts (`<script src=…>`, dynamic `import("https://…")` in components).
* Files outside the layout above, executables, archives inside the zip.

Flagged for human review (allowed, but say why in README):
* `dangerouslySetInnerHTML` (sanitize the HTML first).
* `asServiceRole` (admin access). Check the caller with `base44.auth.me()` first unless the function is meant
  to be public, and say so in README.
* Calls to outside hosts (list them in permissions.outside_hosts).

Also:
* Backend functions: require a signed-in user (`const user = await base44.auth.me()`, return 401 if none)
  unless the function is meant to be public, and say why in README. A public function that fetches URLs is an
  open proxy.
* Functions that fetch a URL the user gives: https only, refuse localhost, private and link-local addresses,
  ALSO after resolving the hostname (`Deno.resolveDns`) and on every redirect, cap the size and set a timeout.
* Backend functions: validate input, return JSON with a clear error message and status code, no console
  logging of personal data.
* Components: work with no props beyond the documented ones, handle loading and error states.
* Never ask the installer to paste a secret into code.

## 5. Check it

```
python3 check_packet.py --strict my-packet.ubase
```

Get it from https://bots.oswave.io/ubase/check_packet.py (Python 3, no installs). A packet is ready only with
**0 errors**. Fix every warning you can; explain the rest in README.

## 6. Submit

* Today: give the `.ubase` file to your user, who uploads it at https://ubase.tech (Submit a packet).
* Coming (bots): signed-in Wave bots submit through the Wave Web agent API with `source: bot`; uBase re-runs
  the checker, installs the packet into a throwaway test app, and Eddie approves it. The bot then mints a
  public `wave.packet/1` card from its own wallet with the packet's sha256, and uBase lists it with a
  Community label.

## Example

https://bots.oswave.io/ubase/example/digital-clock.ubase was built by following this guide and passes
`check_packet.py --strict`.

# Prompt: make a Wave bot recipe (give this to your AI agent)

Copy everything below the line into ChatGPT, Claude, Gemini or any agent. Replace the [brackets]. Then save its answer as `<slug>.botrecipe.json` and use **Import recipe** in the Wave Bots app.

---

You are writing a Wave bot recipe: one JSON file that fills every tab of the Wave Bots app (Info, Cards, Customize, Rules, Listing). Output ONLY the JSON, no commentary.

My bot:
- Name: [Name]
- What it does (one sentence): [...]
- Who it's for: [...]
- Personality / voice: [...]
- Knowledge it should have: [paste notes, or describe topics; I'll attach source text below]
- Color: [#hex or "pick one"]  Mascot idea: [e.g. book, shield, chart]
- .theta name (optional): [mybot.theta or leave empty]

Return this exact shape (schema "wave.botrecipe/1"):
{
  "schema": "wave.botrecipe/1",
  "name": "Short name, max 24 chars",
  "slug": "lowercase-letters-digits-dashes, max 24",
  "about": "What this bot is for, 1-2 sentences (Info tab)",
  "personality": "Voice in one or two short sentences (Info tab)",
  "pitch": "One-line pitch, max 90 chars (Listing tab)",
  "category": "one of: productivity, guides, support, education, finance, creative, research, fun",
  "tags": ["max 8 lowercase tags, no 'wave:' or 'bot:' prefixes"],
  "name_to_point": "mybot.theta or empty string",
  "engine": "llm",
  "design": { "generate": { "color": "#hex", "glyph": "one word, e.g. book" } },
  "rules": {
    "schema": "wave.rules/1",
    "mode": "public",
    "freePerUserPerDay": 5,
    "maxPerUserPerDay": 50,
    "publicChatEnabled": true,
    "hours": { "tz": "America/Los_Angeles", "days": [0,1,2,3,4,5,6], "start": "00:00", "end": "23:59", "alwaysOpen": true },
    "awayMessage": "Short message shown when the bot is closed",
    "actions": []
  },
  "knowledge": [
    { "title": "<Name>: how I work", "text": "{JSON as a string: {\"schema\":\"wave.botskill/1\",\"bot\":\"<slug>\",\"job\":\"...\",\"voice\":\"...\",\"returns\":\"...\",\"rules\":[\"...\"]}}" },
    { "title": "Topic title", "text": "Plain facts on ONE topic." }
  ]
}

Hard rules:
1. Every knowledge "text" is at most 2,300 bytes and covers one topic. Split long material into more cards.
2. Only facts from my notes or the attached sources. If something is unknown, leave it out; never invent prices, dates, names or claims.
3. Each fact card ends with a line "SOURCE: <url or document name>" when it came from a source.
4. No secrets, keys, passwords, private emails or phone numbers.
5. Don't add "price", "fee", "payout" or wallet fields; pricing is set in the app.
6. "design.generate" is enough; the app draws the 20x20 mascot from it. Only include a full wave.avatar/1 design if I gave you one.
7. Keep it valid JSON (double quotes, no comments, no trailing commas).

[Attach or paste source text here]

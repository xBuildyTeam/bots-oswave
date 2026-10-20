# Wave Utility Bots v0.1: five productivity bots that chain

Drafted 2026-10-20. Five small bots, each doing one job, that share one JSON envelope (`wave.task/1`). Any bot's answer is a valid input for the next, so they can be called alone or chained into a bigger task. Recipes in this folder are ready for the Publish Bot Wizard (Import recipe, then Check only).

| Bot | Name | Job | Returns | Engine |
|---|---|---|---|---|
| Clerk | clerk.bots.theta | Messy notes, emails or transcripts into tasks, people, dates, decisions | `wave.items/1` | Lite AI (Qwen3 1.7B + harness), Flash fallback |
| Planner | planner.bots.theta | Goal or task list into a dated schedule with dependencies | `wave.plan/1` | Lite AI + date helpers, Flash fallback |
| Tally | tally.bots.theta | Budgets, estimates, conversions, TFUEL costs, computed in code | `wave.tally/1` | Lite AI; math always in the sandbox |
| Scribe | scribe.bots.theta | The finished email, summary, post or brief | `wave.draft/1` | Qwen3.8-Flash |
| Checker | checker.bots.theta | Checks every claim in a draft against its sources | `wave.check/1` | Code checks first, Flash for wording |

## 1. The shared envelope: wave.task/1

```json
{
  "schema": "wave.task/1",
  "task_id": "t_8f2c",
  "goal": "Turn Monday's launch meeting into a dated plan, a budget and a follow-up email",
  "step": 3,
  "bot": "tally.bots.theta",
  "next": "scribe.bots.theta",
  "status": "ok",
  "questions": [],
  "input": { "from_step": 2 },
  "output": { "kind": "wave.tally/1", "...": "..." },
  "history": [
    { "step": 1, "bot": "clerk.bots.theta", "kind": "wave.items/1", "sha256": "..." },
    { "step": 2, "bot": "planner.bots.theta", "kind": "wave.plan/1", "sha256": "..." }
  ],
  "refs": ["v3:12"],
  "cost": { "step_tfuel": 0.2754, "total_tfuel": 0.8262, "quote_tfuel": 1.377 }
}
```

Rules every bot follows:
1. Pass on fields you don't understand. Never drop them.
2. Every fact you add names its source: a step and field (`2:steps.s3.end`) or a card (`v3:N`).
3. Dates are ISO 8601 with a timezone. Money and counts are numbers.
4. If you can't do your part, return `status: "needs_input"` with `questions`. Never guess.
5. Utility bots take no outside actions. They read and return JSON (rules `actions: []`). Sending the email is the caller's job, after Checker passes.

The caller (any AI over MCP, or the Wave app) drives the chain with the existing store tools: `bots_discover` to find the bots, `bots_inspect` for prices, `bots_call` once per step, passing the previous envelope. No new MCP tool is needed. `quote_tfuel` is set before step 1, so the price of the whole chain is known up front ("every answer states its price").

## 2. What each bot returns

**Clerk, wave.items/1**: `tasks[] {id, text, owner|null, due|null, quote}`, `people[]`, `dates[]`, `decisions[]`, `open_questions[]`. Every task carries the exact words it came from. Relative dates ("next Friday") are resolved in code against the input's date and timezone, or asked for.

**Planner, wave.plan/1**: `deadline`, `tz`, `working_days`, `steps[] {id, task, title, owner, depends_on, start, end, hours}`, `critical_path`, `slack_days`, `conflicts[]`. Date math always runs in code. If the work doesn't fit, the deadline stays and the shortfall is listed.

**Tally, wave.tally/1**: `currency`, `lines[] {label, step, qty, unit, rate, amount}`, `total`, `code`, `assumptions[]`. The model writes the formula and the sandbox runs it. The code ships in the answer, so anyone can re-run it. Missing rates are asked for, never made up.

**Scribe, wave.draft/1**: `format`, `tone`, `subject`, `body`, `claims[] {text, from}`. Every date, number, name and promise in the body is listed in `claims` with its source. Scribe adds no facts of its own.

**Checker, wave.check/1**: `verdict pass|fail`, `results[] {claim, status supported|contradicted|unsupported, evidence, note}`, `fixes[]`. Dates, numbers and names are compared in code, exactly. Cards are hash-checked through `waveApi?action=check` before they count. Any contradicted or unsupported claim fails the draft. Checker never rewrites. It lists fixes for Scribe.

Because Scribe must list its claims and Checker compares them in code, the last step is mostly deterministic. That's the "verifiable memory reduces hallucinations" pitch working inside one chain.

## 3. Worked chain: "handle the follow-up from this meeting"

1. **Clerk** reads the transcript: 6 tasks, a launch date of 2026-11-13, 2 open questions.
2. **Planner** schedules the 6 tasks backward from 2026-11-13 on working days: critical path s1, s3, s6, 2 slack days.
3. **Tally** prices the plan: 34 hours at $85 plus $400 ads = $3,290, with the code shown.
4. **Scribe** drafts the email: "Launch is Friday, Nov 13. Budget is $3,290..." with each claim pointing at `2:deadline` and `3:total`.
5. **Checker** passes 7 of 7 claims. If Scribe had written "$3,920", Checker fails it as contradicted (`3:total` = 3290) and lists the fix.

Cost: 5 × 0.2754 = **1.377 TFUEL** for the whole chain, shown before step 1. Shorter chains are cheaper: Scribe then Checker is 0.5508.

## 4. Pricing and rules (same for all five)

- Paid mode: fee 0.12 + AI cost 0.15, then the Wave 2% fee = **0.2754 TFUEL per answer** (above the 0.27 minimum).
- 5 free answers per user per day per bot; 50 max per user per day; 20 TFUEL daily cap on free answers.
- Payout to bots.theta, paid out daily. Always open. Actions: none.
- Lite AI bots (Clerk, Planner, Tally) can run on the phone under Wave Wallet AI later. Their AI cost could drop then, which would lower the price. Wave sets AI cost, so that's a later config change, not a recipe change.

## 5. What gets minted

Per bot: mascot (`wave.avatar/1`, with blink, talk and thinking frames), rules (`wave.rules/1`), listing, and one "how I work" card (`wave.botskill/1`, the job, output shape and rules). The shared `wave.task/1` card is in every recipe, but the wizard reuses identical cards by sha256, so it's minted once.

21 cards in total, all under 1.5 KB. **Estimated ~25 TFUEL** for all five bots (the wizard gives the exact figure in Check only).

## 6. Before publishing

1. The names clerk/planner/tally/scribe/checker.bots.theta don't exist yet. They need to be created under bots.theta by its owner (treasury 0xcb20…1894). The wizard can mint without them and point the names afterward.
2. The bot runtime needs to honor `wave.task/1`: pass the envelope through, append `history`, and add up `cost`. That's a small builder change for the bot service (not sent; needs your OK).
3. Mascots are first drafts (20×20, one colour per bot with an icon on the belly: clipboard, calendar, plus/equals, quill, check mark). Edit them in the Bot Designer if you want.
4. Test before going live: run the worked chain in section 3 through each bot, including the wrong "$3,920" draft, and confirm Checker fails it.

## Files
- `clerk.botrecipe.json`, `planner.botrecipe.json`, `tally.botrecipe.json`, `scribe.botrecipe.json`, `checker.botrecipe.json`: import into the Publish Bot Wizard.
- `mascots.json`, `mascots-preview.png`: the five mascots.

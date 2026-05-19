# CAD Agent Pipeline — Email Trigger Templates

Send any of these emails to: **developmentihpc@gmail.com**
The pipeline runs automatically and replies with the finished PowerPoint attached.

---

## Format

```
Subject: RUN: <Country> / <Sector> / <Workflow>
Body:    (optional parameters — see Advanced section)
```

**Workflow values:** `needs` · `proposal` · `external`

---

## Country Needs Assessment (`needs`)
*9 agents · 13 slides · ~4 min*
Identifies development gaps, benchmarks vs. SDGs, ranks priority areas.
No project proposals — analysis and evidence only.

```
Subject: RUN: Ethiopia / Health & Nutrition / needs
```
```
Subject: RUN: Yemen / WASH & Food Security / needs
```
```
Subject: RUN: Somalia / Education & Livelihoods / needs
```
```
Subject: RUN: Jordan / Governance & Economic Inclusion / needs
```
```
Subject: RUN: Sudan / Health & WASH / needs
```
```
Subject: RUN: Nigeria / Energy & Infrastructure / needs
```
```
Subject: RUN: Somaliland / All sectors / needs
```

---

## Development Proposal (`proposal`)
*11 agents · 16 slides · ~6 min*
Designs 3 project concepts with budgets, KPIs, risk matrix, and implementation timeline.
Requires a sector and indicative budget.

```
Subject: RUN: Ethiopia / Health & Nutrition / proposal
```
```
Subject: RUN: Jordan / Education & Youth Employment / proposal
```
```
Subject: RUN: Yemen / WASH & Resilience / proposal
```
```
Subject: RUN: Rwanda / Agriculture & Livelihoods / proposal
```
```
Subject: RUN: Pakistan / Education & Gender / proposal
```
```
Subject: RUN: Bangladesh / Climate Resilience & WASH / proposal
```

---

## External Project Assessment (`external`)
*3 agents · Scorecard output · ~2 min*
Scores externally submitted projects against 13 criteria.
Returns ranked list with approve / revise / reject recommendation per project.

```
Subject: RUN: Kenya / Renewable Energy / external
```
```
Subject: RUN: Uganda / Health Systems / external
```
```
Subject: RUN: Morocco / Vocational Training / external
```

---

## Advanced — Body Parameters (optional)

Add any of these lines in the **email body** to override defaults:

```
audience: Senior Leadership & Donor Partners
budget: USD 20-35 million
horizon: 4 years
projects: 2
```

**Full example:**
```
Subject: RUN: Ethiopia / Health & Nutrition / proposal

audience: UAE Aid Agency Board
budget: USD 25-40 million
horizon: 5 years
```

---

## What You Get Back

**Email reply** within 5-10 minutes containing:
- ✅ / ⚠️ / ❌ Editor verdict (READY / READY WITH CAVEATS / NOT READY)
- 📎 Finished `.pptx` attached
- Summary table of each agent's output excerpt

**Local files** saved to `agent_outputs/` folder:
- One `.txt` per agent (full reasoning preserved)
- The `.pptx` file
- `_result.html` — browser preview of the result email

---

## Sector Reference

Use any of these sector names (or combine with `&`):

| Sector | Example trigger |
|---|---|
| Health | `/ Health & Nutrition /` |
| Education | `/ Education & Youth /` |
| WASH | `/ WASH & Sanitation /` |
| Food Security | `/ Food Security & Agriculture /` |
| Energy | `/ Energy & Infrastructure /` |
| Livelihoods | `/ Livelihoods & Economic Inclusion /` |
| Governance | `/ Governance & Institutional Capacity /` |
| Gender | `/ Gender & Social Inclusion /` |
| Climate | `/ Climate Resilience & Environment /` |
| All | `/ All sectors /` |

---

## Setup Checklist

- [ ] `ANTHROPIC_API_KEY` added to `.env`
- [ ] `GMAIL_APP_PASSWORD` added to `.env` (see: myaccount.google.com/apppasswords)
- [ ] IMAP enabled in Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
- [ ] `start_watch.bat` running on your PC

---

## Troubleshooting

**No reply after 10 min:**
- Check the terminal window running `start_watch.bat` for error messages
- Verify IMAP is enabled in Gmail settings
- Check `ANTHROPIC_API_KEY` is correct in `.env`

**"IMAP login failed":**
- Enable IMAP in Gmail: Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
- Make sure you're using the App Password, not your regular Gmail password

**PPT not attached:**
- Node.js or pptxgenjs not installed — agent outputs still saved as `.txt` in `agent_outputs/`
- Install: `npm install -g pptxgenjs`

**"NOT READY" verdict:**
- The Editor agent flagged quality issues
- Check `agent_outputs/countryname_workflow_editor.txt` for the specific issues
- Re-trigger — the research agent may have had data gaps on the first run

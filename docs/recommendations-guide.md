# Cadenza Insights & Recommendations — Learning Guide

A teaching walkthrough of the three insights surfaced in the Cadenza dashboard,
the recommendations each one drives, and how to talk about them in a RevOps
interview.

This guide decodes the jargon, explains the *why* behind each recommendation,
and gives you a one-sentence "interview pitch" you can use to summarize each
recommendation under pressure.

---

## Insight 1 — Self-Serve Promo cohort churns ~2× faster

### The business context

A Q3 2024 promotional campaign acquired customers through the Self-Serve channel
at a discount. Twelve months later, that cohort churns at roughly twice the rate
of customers acquired through other channels. Surface retention metrics
(NRR ~108%, GRR ~91%) look healthy — but the segment-level decomposition tells
a different story.

This is the most important kind of RevOps finding: **a headline metric that
masks a problem until you decompose it.**

### Recommendation 1: Tech-touch CSM motion for the cohort

**Decoding the jargon.** CSM = Customer Success Manager. The team responsible
for keeping customers engaged and renewing. "Tech-touch" means the CSM motion
is delivered through automation (email sequences, in-app prompts, scheduled
webinars) rather than 1:1 human coverage. The reason for tech-touch rather
than human: Self-Serve Promo customers have low ACV (annual contract value),
so putting a human CSM on every one of them isn't unit-economic.

**The tactics inside the recommendation:**

- **Contract-end outreach 60 days early.** If you wait until the contract
  expires, the customer has already mentally decided.
- **Value-realization check-ins.** Scheduled touchpoints (automated usage
  summaries, ROI dashboards) to confirm they're getting value.
- **Expansion offers.** Counterintuitively, customers who *expand* (buy more
  seats / upgrade) churn less because they're more invested.

**Interview pitch.** "Self-Serve Promo customers churn 2× faster than other
channels. I'd build a tech-touch CSM motion targeted at that cohort —
automated contract-end outreach 60 days early, value-realization prompts,
and expansion offers. The tech-touch part matters because their ACV doesn't
support 1:1 human coverage."

### Recommendation 2: Channel-quality scoring partnered with marketing

**Decoding the jargon.** Marketing teams typically optimize for *leads* or
*first-month MRR* (revenue at signup). That ignores whether the customer
sticks around. Channel-quality scoring assigns each acquisition channel a
retention-quality score and weights marketing's KPIs by it.

**The mechanism.** Track M6 retention rate (or M3, or M12 — pick a horizon)
by channel. $10K of Self-Serve Promo first-month MRR is *worth less* than
$10K of Outbound first-month MRR if Self-Serve Promo retains worse.
Marketing's bonuses, channel budgets, and CAC payback models all shift to
reflect retention-adjusted revenue.

**Why this is a RevOps move.** This brings retention data *back upstream*
to marketing. RevOps sits between sales, marketing, and CS — bringing data
across those boundaries is exactly the job. A hiring manager will recognize
this as "thinking past the funnel handoff."

**Interview pitch.** "I'd partner with marketing to build channel-quality
scoring — weight new-customer acquisitions by M6 retention rate, not just
first-month MRR. Marketing optimizes for what they're measured on. If they're
measured on retention-quality, they'll change which channels they spend in."

### Recommendation 3: Tighter promo gating

**Decoding the jargon.** The hypothesis is that discounts attract
bargain-hunters who don't really commit to the product. "Gating" the promo
means restricting eligibility — only customers who've already shown product
engagement (e.g., 90 days of consistent logins, feature use) qualify for the
discount. This shifts the promo from "acquisition incentive" to
"retention/expansion incentive."

**The friction.** Some marketing teams will resist because gating tanks their
acquisition numbers. RevOps's job here is to bring the data — show that gated
promos retain 2-3× better than ungated promos, so the lifetime-value tradeoff
is positive even if acquisition slows.

**Interview pitch.** "On future promotional campaigns, I'd gate the discount
behind product engagement — require 90 days of activity before eligibility.
The hypothesis is the original promo attracted bargain-hunters. Gating filters
them out and re-positions the offer as a retention or expansion incentive
rather than acquisition."

---

## Insight 2 — Mid-Market deals stall in POC ~2× longer

### The business context

A new-business sales cycle moves through stages:
**Discovery → Qualification → Proof of Concept → Negotiation → Closed.**
The POC stage is where the customer tests the product before committing.
SMB deals breeze through POC in days. Enterprise deals take longer but
are tightly managed. Mid-Market deals — the segment in between — stall
in POC roughly twice as long as either neighbor, and their POC → Negotiation
conversion is markedly worse.

**The diagnosis.** The POC motion is built for either end of the spectrum
(SMB = fast/self-guided, Enterprise = custom/white-glove). Mid-Market falls
in the gap. The fix is a Mid-Market-specific playbook plus pipeline
discipline.

### Recommendation 1: Mid-Market-specific POC playbook

**Decoding the jargon.**

- **SE** = Sales Engineer (also Solutions Engineer / Solutions Consultant).
  A technical seller who supports the AE (Account Executive — the commercial
  seller) on technical questions and runs the POC.
- **Time-boxed to 30 days** = the POC has a hard end date that forces a
  yes/no decision. Without a time-box, POCs drift indefinitely.
- **Defined success criteria agreed and emailed back to the buyer up front**
  = at POC start, you and the buyer agree on "if X, Y, Z happen, you'll buy."
  Then you email it back so it's in writing. This is the antidote to scope
  creep ("we need *one more feature* before we'll commit").

**Why it works.** POC stall is almost always either (a) the buyer hasn't
defined what "success" looks like, or (b) the seller has no technical support
to actually demonstrate value. The playbook addresses both.

**Interview pitch.** "Mid-Market POCs stall because the segment falls between
SMB's self-serve motion and Enterprise's white-glove motion. I'd build a
Mid-Market-specific playbook: dedicated SE coverage, a 30-day time-box, and
written success criteria up front. The criteria piece is what stops scope
creep."

### Recommendation 2: Segment routing — define and route correctly

**Decoding the jargon.** "Segment routing" is how deals get assigned to sales
motions and reps. Is this account SMB, Mid-Market, or Enterprise? Which rep
works it? Which playbook applies? The recommendation is to define Mid-Market
by *clear thresholds* (revenue band, headcount, tech stack signals) and route
those deals to a dedicated SE pod — so they're not handled as either
"overgrown SMB" (no SE, self-serve) or "junior Enterprise" (heavy custom
motion that's overkill).

**Why this is RevOps.** Segment definitions, routing rules, and the
operational discipline to monitor whether routing matches reality — that's
squarely RevOps territory. Marketing, Sales, and CS all have opinions on
segmentation; RevOps owns the source of truth.

**Interview pitch.** "Beyond the playbook, the upstream issue is segment
routing. I'd define Mid-Market by explicit thresholds — say 100-1000
employees, or $10M-$100M revenue — and route those accounts to a dedicated
SE pod. Otherwise Mid-Market deals end up in either the SMB or Enterprise
motion and neither one is built for them."

### Recommendation 3: POC exit gates

**Decoding the jargon.** An "exit gate" is a forced checkpoint. If a deal
stays in POC past 45 days, an alert fires and a manager has to make a call:
**escalate** (push it up — maybe the deal needs C-level engagement),
**re-scope** (maybe the POC was too ambitious — shrink it), or
**disqualify** (maybe this deal is dead and the team should stop spending
effort on it).

**Why it matters.** Reps will keep deals "in POC" indefinitely because
calling a deal dead feels worse than letting it linger. Pipeline reports get
clogged with zombie deals that inflate open pipeline but never close. A
forced review forces the honest call.

**Interview pitch.** "I'd add a 45-day exit gate on POC. Past that, the deal
triggers a forced review — escalate, re-scope, or disqualify. This is
pipeline hygiene. Reps don't volunteer to call deals dead, so the process
has to do it for them."

---

## Insight 3 — Ramp is ~9 months, not 6

### The business context

When a new sales rep joins, they don't carry full quota from day one. They
need time to learn the product, build pipeline, and close deals — that's
"ramping." Industry convention is to assume reps reach full productivity at
month 6. Cadenza's actual ramp curve, charted longitudinally across the
team, hits full productivity around month 9.

That gap matters operationally. Hiring lead times, comp plan design, and
performance reviews are all calibrated against the ramp assumption. If the
assumption is wrong by 3 months, three downstream things break: you hire
too late, you pay reps as if they're failing, and you fire reps who are
actually tracking-to-curve.

### Recommendation 1: Adjust hiring lead times

**Decoding the jargon.** "Backfill" = replacing a rep who has left. If a rep
gives notice and ramp is 9 months, you need their replacement *already ramped*
by the time you need productive capacity. Your hiring funnel adds time on top
(recruit → interview → offer → start → ramp). So plan backwards from when
the capacity is needed.

**The math.** If you assumed 6-month ramp and need productive capacity by Q3,
you'd start recruiting ~Q1. If actual ramp is 9 months, you should have
started Q4 of the prior year. Three months of lost capacity at the rep level
adds up to material missed bookings at the team level.

**Interview pitch.** "If actual ramp is 9 months instead of 6, hiring lead
times have to stretch with it. I'd push backfill recruiting to start ~3 months
earlier so the new rep is productive when capacity is needed, not 3 months
after."

### Recommendation 2: Match the quota ramp schedule to the real curve

**Decoding the jargon.** "Ramped quota" means a new rep's quota grows in
stages, not full from day one. Standard practice in SaaS is something like
25% / 50% / 100% across the first 9 months (or whatever the ramp duration is).

**Why this is operationally important.** If a rep is at 50% of full quota in
month 4, and you compare against 100%-quota expectations, they look like
they're failing. Their commission check reflects that. They quit (or
disengage), which makes the ramp problem worse for the team. Matching the
quota ramp schedule to the actual ramp curve removes that doom loop.

**Interview pitch.** "Comp design has to match the ramp curve. If a rep is
tracking to 50% in month 4 and that's on-curve, they should be paid as
on-curve, not as failing. I'd push for a 25/50/100 schedule over 9 months
rather than the standard 6-month front-load."

### Recommendation 3: Build the ramp curve into performance reviews

**Decoding the jargon.** Performance reviews look at quarterly attainment.
Without a ramp framework, managers compare every rep against full-quota
expectations — which means ramping reps always look like underperformers.
The recommendation is to build the ramp curve into the review process so
managers can answer: *"is this rep underperforming, or are they on-curve?"*

**Why this is the operational kicker.** The analytical finding (9-month ramp)
doesn't change anything if managers still flag ramp-cohort reps as failures
in their first quarterly review. The reps quit. You backfill. The ramp
problem perpetuates. Building the curve into the review framework breaks the
cycle.

**Interview pitch.** "The analytical finding has to land in the
performance-review framework, or it doesn't change anything. I'd build the
ramp curve into reviews so managers can separate 'tracking to ramp' from
'underperforming.' Reps at 50% in month 4 are on-curve; that should be visible
to the manager, not hidden behind a quota comparison."

---

## What these recommendations demonstrate

Each insight has the same shape: a *finding*, three *operational responses*,
and a connection back to a real GTM function.

The pattern hiring managers are listening for:

1. **You can decompose a metric.** NRR looks healthy; the channel cut shows
   the problem. Win rate looks healthy; the segment cut shows POC stall.
   Average rep attainment looks healthy; the tenure cut shows a 9-month ramp.
2. **You connect findings to operational consequences.** Not just "we should
   monitor this," but "here's what we'd change about how we work tomorrow
   morning."
3. **You think across functions.** Marketing-with-CS for channel scoring;
   AEs-with-SEs for POC playbooks; recruiting-with-comp-with-performance-
   management for ramp.

If you can walk through any of these three insights and stay grounded in the
*what would we actually change tomorrow morning* layer, you're demonstrating
RevOps thinking.

---

## Glossary

| Term | Definition |
|---|---|
| ACV | Annual Contract Value. The yearly recurring revenue of a customer. |
| AE | Account Executive. The commercial seller responsible for closing deals. |
| Backfill | Replacing a rep who has left the team. |
| CAC | Customer Acquisition Cost. Total sales+marketing spend divided by new customers acquired. |
| Cohort | A group of customers (or deals, or reps) defined by some shared starting point. |
| CSM | Customer Success Manager. Owns post-sale customer engagement and renewals. |
| Exit gate | A forced-decision checkpoint in a sales process. |
| GRR | Gross Revenue Retention. Revenue retained from existing customers, excluding expansion. |
| GTM | Go-to-Market. The combined sales + marketing + CS motion. |
| MRR | Monthly Recurring Revenue. |
| MQL / SQL | Marketing-Qualified Lead / Sales-Qualified Lead. Lifecycle stages before opportunity creation. |
| NRR | Net Revenue Retention. Includes expansion — can exceed 100%. |
| POC | Proof of Concept. A trial / pilot stage in a sales cycle. |
| Ramp | The period over which a new rep grows from zero productivity to full. |
| Ramped quota | A quota schedule that grows in stages during a rep's ramp period. |
| RevOps | Revenue Operations. The function that owns process, data, and tooling across sales, marketing, and CS. |
| SE | Sales Engineer (Solutions Engineer / Solutions Consultant). Technical seller supporting POCs and integrations. |
| Segment | A grouping of accounts by size — typically SMB, Mid-Market, Enterprise. |
| Tech-touch | A low-touch customer success motion delivered through automation rather than 1:1 human coverage. |

---

*Companion to the Cadenza Insights & Recommendations dashboard. Use this guide
to prepare interview talking points; the dashboard itself is the live
demonstration.*

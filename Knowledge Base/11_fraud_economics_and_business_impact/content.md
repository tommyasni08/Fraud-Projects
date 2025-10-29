# 📘 Module 11 - Fraud Economics & Business Impact

(How organizations quantify, control, and justify fraud decisions)

## 0 TL;DR

Fraud prevention isn’t just about stopping bad actors — it’s about optimizing the business.
The goal is not zero fraud (too much friction kills revenue), but the optimal fraud level that maximizes net business value.
This requires:

- Quantifying fraud impact in financial terms,
- Modeling safety vs. friction trade-offs,
- Defining ownership of KPIs across Growth, Risk & CX,
- Building decision economics frameworks to guide controls and investments.

## 1. Why Fraud Economics Matters

Fraud teams succeed when they can answer:

“How much loss should we tolerate to maximize profit and growth?”

Fraud interacts with:

- Revenue (conversion, approvals, repeat use),
- Costs (losses, chargebacks, disputes, reviews),
- Trust (brand reputation, compliance).

The key is profit optimization, not absolute fraud elimination.

## 2. Fraud Cost Categories

| Cost Type            | Examples                                          |
| -------------------- | ------------------------------------------------- |
| **Direct Losses**    | Chargebacks, refunds, promo leakage, stolen goods |
| **Indirect Losses**  | Support & investigation labor, legal costs        |
| **Hidden Costs**     | Model degradation, bad reputation, churn          |
| **Opportunity Loss** | Declined good customers, friction drop-offs       |

➡ Fraud leaders must track all of these in decision-making.

## 3. The Safety–Friction Trade-Off

Fraud controls increase safety but reduce good-user success.

| Decision          | Fraud ↓ | Revenue ↓ | CX ↓ |
| ----------------- | ------- | --------- | ---- |
| Add more friction | ✅      | ❌        | ❌   |
| Reduce friction   | ❌      | ✅        | ✅   |

Goal: Balance fraud catch rate and customer experience.

## 4. Decision Economics Framework

For each decision (allow / challenge / block), estimate:
EV = (Pgood x Revenue) - (Pfraud x Loss) - (FrictionCost)

→ Select action that maximizes Expected Value.

Example:

| Option  | P(good) | Revenue | P(fraud) | Fraud Loss | EV         |
| ------- | ------- | ------- | -------- | ---------- | ---------- |
| Approve | 0.97    | 10      | 0.03     | -100       | **7.0** ✅ |
| Step-up | 0.97    | 9       | 0.03     | -100       | 5.91       |
| Decline | 0.97    | 0       | 0.03     | 0          | 0          |

🎯 Choose “Approve” even with non-zero fraud risk → this is counterintuitive, but financially optimal.

## 5. Fraud as Part of Revenue Strategy

A small, managed amount of fraud is healthy if:

- It enables frictionless experiences
- It grows market share faster than fraud loss grows

This is why Uber, Grab, Shopee scale rapidly:
They invest heavily in fraud later, after product-market fit.

Thus, fraud is a business lever, not just a risk.

## 6. KPIs: What Fraud Teams Actually Own

Fraud teams must align with business goals:
| KPI | Meaning |
| ---------------------------- | ---------------------------------------- |
| **Fraud loss % GMV** | Fraud leakage normalized for growth |
| **False Positive Rate** | Good users wrongly blocked |
| **Approval Rate** | Conversion → revenue impact |
| **Safety-Friction Frontier** | Curve showing best achievable trade-offs |
| **ROI of Controls** | Benefit ($ saved) / Cost ($ spent) |
| **Appeal Overturn Rate** | Proxy for fairness & trust |
| **Detection-to-Block Time** | Operational efficiency |

A great fraud team balances these, not maximizes just one.

## 7. Organizational Roles & Ownership

| Function           | Goal                         | Conflict with Fraud         |
| ------------------ | ---------------------------- | --------------------------- |
| Growth / Marketing | Max conversion, promo impact | ↑ fraud risk                |
| Risk / Fraud       | Minimize fraud losses        | ↑ friction, ↓ revenue       |
| CX / Support       | Max customer trust           | May over-refund             |
| Product            | Smooth UX                    | May expose vulnerabilities  |
| Finance            | P&L protection               | Invest only with proven ROI |

✅ Leaders align them via shared KPIs (e.g., Net Good Users, Approval Rate @ target loss %)

## 8. Fraud Investment ROI

Executives approve budgets only if fraud tools:

- Reduce losses more than they cost
- Improve unit economics (LTV/CAC, contribution margin)

Example rationalization:

“Our new ML model reduces fraud loss by
-$5M annually, costs $1M, → 4× ROI.”

Fraud leaders must speak CFO language.

## 9. Risk Appetite & Policy

Companies explicitly set acceptable fraud thresholds:
| Scenario | Typical Target |
| ---------------------------- | --------------------------------------- |
| Early-stage startup | 3–10% loss acceptable (growth priority) |
| Established marketplace | 0.5–2% loss target |
| Regulated financial services | <0.1% loss (high scrutiny) |

➡ “Zero tolerance” = expensive overkill.

## 10. Model Governance & Compliance

Fraud models require:

- Explainability (for regulators & appeals)
- Drift monitoring
- Bias & fairness checks
- Version control + audit trail
- Human review for edge cases

Fraud systems are risk systems, not pure tech.

## 11. Operational Excellence — The Fraud Funnel

Flow:
Attempts → Score → Action (allow/challenge/block) → Appeal → Recovery → Label feedback

Analysts monitor:

- Drop-offs (lost $$) at each step
- Where leakage (fraud passed) occurs
- Where friction highest for good users

This visualizes true P&L impact, not just model accuracy.

## 12. Common Pitfalls & How to Avoid

| Pitfall                      | Fix                                    |
| ---------------------------- | -------------------------------------- |
| “Block everything risky”     | EV-based decisioning; dynamic friction |
| Misaligned KPIs              | Shared Ownership (Fraud × Growth × CX) |
| One-size-fits-all thresholds | Segment by risk cohort                 |
| Delayed feedback loops       | Real-time labels & retraining          |
| Over-automation              | Human-in-loop governance               |
| Focusing only on the bad     | Optimize **good user success** too     |

## 13. Strategic Maturity Curve

| Stage         | Tools                           | Focus                  |
| ------------- | ------------------------------- | ---------------------- |
| 1️⃣ Reactive   | Manual, rules-only              | Stop known fraud       |
| 2️⃣ Proactive  | ML scoring + feedback loops     | Reduce loss rate       |
| 3️⃣ Optimizing | EV-based orchestration          | Improve profit & CX    |
| 4️⃣ Strategic  | Fraud informs product & pricing | Business growth driver |

## 14. Key Takeaways

- Fraud prevention = business optimization, not policing.
- The goal = maximize net economic value, not minimize fraud.
- Fraud and Growth must be partners, not enemies.
- The best fraud systems reduce losses while enabling revenue.

A truly mature fraud function is a profit maximizer.

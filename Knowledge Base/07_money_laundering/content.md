# 📘 Module 7 - Money Laundering

## 0 TL;DR

Money laundering (ML) disguises the origin of illicit funds through **placement → layering → integration**. Modern flows often traverse **instant payments, P2P wallets, crypto off-/on-ramps, and marketplaces**, using **mule accounts** (witting or unwitting) and **collusive webs** to fragment and obscure trails (“structuring/smurfing”).
Detection blends **rules (typologies), graph analytics,** and **anomaly models**—all under strict **regulatory requirements** (KYC/KYB, sanctions screening, SAR/STR filings, auditability, explainability).

## 1. Definition & Scope

- **Money Laundering (ML)**: Concealing criminal proceeds and making them appear legitimate.
- **Mule Account**: Account (person or business) used to receive/move funds for criminals—witting, unwitting, or complicit-for-hire.
- **Three Stages**:
  - **Placement**: Introducing illicit cash into the financial system (cash deposits, prepaid cards, cash-intensive merchants).
  - **Layering**: Creating distance via transfers, trades, conversions (A2A hops, crypto swaps, cross-border wires, trade invoices).
  - **Integration**: Reintroducing funds as “legit” (payrolls, invoices, asset purchases, loans, gambling winnings).
- **Where it appears**: Banks/fintechs, P2P wallets, exchanges, merchant acquirers, marketplaces, remittances, and increasingly platform payouts (creator/driver/merchant).

## 2. Attacker Motivations & Modern Realities

- **Speed & Irreversibility**: Instant rails (RTP, Faster Payments) let launderers move funds before detection.
- **Global Arbitrage**: Jurisdictional gaps, weak KYC/KYB in certain corridors, nested relationships.
- **Blend with Fraud**: Proceeds from ATO, scams, promo/refund abuse laundered through mule webs.
- **Crypto + Hybrid routes**: Cash → exchange/on-ramp → swap/bridge → off-ramp → bank—interlaced with P2P hops.

## 3. Common Typologies (What investigators see)

- **Structuring / Smurfing**: Many small deposits/transfers just below reporting thresholds.
- **Funnel Accounts**: Multiple sources feed one account, which quickly forwards funds.
- **Pass-through / Velocity Mules**: Incoming → rapid outflow (near 100% turnover) with minimal balance.
- **Round-tripping**: Funds leave and re-enter via different channels (offshore, crypto, e-money).
- **Trade-Based ML**: Over/under-invoicing, ghost shipments, marketplace seller webs.
- **Money Service Businesses (MSBs) abuse**: Poorly supervised remitters as conduits.
- **E-commerce & payout laundering**: Shell “merchants” process fake sales to justify deposits.
- **Charity/NGO misuse**: Donations concentrated from suspicious sources then dispersed.
- **High-risk geographies / sanctioned parties**: Routing via intermediaries to obfuscate nexus.

## 4. Mule Networks (Recruitment & Behavior)

- **Recruitment**: Social media, job ads (“work-from-home, payment processing”), romance/investment scams (victims become mules), student communities.
- **Types**:
  - **Unwitting mules**: Believe they’re processing legitimate payments.
  - **Witting/complicit mules**: Paid % of throughput.
  - **Industrial rings**: Coordinated with device farms, synthetic KYB entities, and scripted payouts.
- **Behavioral hallmarks**:
  - New account with rapid inbound from many unrelated sources; immediate outbound to new beneficiaries.
  - Low balance / high turnover, no genuine consumer activity (no bills, no typical spend).
  - Repeated beneficiary churn; use of common narratives (“family help”, “goods”, vague memos).

## 5. Regulatory & Policy Backbone (why it’s different from ordinary fraud)

- **KYC/KYB & CDD/EDD**: Risk-based verification; ongoing monitoring.
- **Sanctions/Watchlists**: OFAC/UN/EU lists; PEP & adverse media screening.
- **SAR/STR filings**: Suspicion-based reporting to FIUs; confidentiality and timeliness required.
- **Auditability & Explainability**: Decisions must be defensible to regulators; black-box ML alone is insufficient.
- **Risk Assessment**: Enterprise-wide AML risk assessment (products, geographies, customers, channels).

## 6. Signals & Data to Capture (Analyst Checklist)

**Identity & Profile**

- KYC/KYB quality, document/beneficial ownership verification, expected activity profile (declared purpose, occupation, turnover).

**Payments & Accounts**

- Amounts, counterparties, rails, currencies, MCCs; velocity (in/out counts), turnover ratio (outflow/inflow), balance stability, beneficiary diversity, time-to-outflow.

**Counterparty & Network**

- Shared devices/IPs, address/phone reuse; counterparty risk (age, KYC tier), known mule markers, graph centrality.

**Geography & Corridor**

- Country risk ratings, cross-border links, corridor typologies (high-risk paths).

**Crypto & Hybrid Signals (if applicable)**

- On-/off-ramp entities, exchange wallet tags, chain analytics risk flags, mixer/tumbler exposure, rapid cross-chain swaps.

**Narrative/Evidence**

- Payment memos, invoice metadata, KYB docs, proof-of-goods inconsistencies, support/chat artifacts.

## 7. Feature Engineering (High-signal examples)

**Behavioral & Flow**

- `inflow_count_7d/30d`, `outflow_count_7d/30d`, `avg_time_to_outflow`, `turnover = total_out / total_in`
- `peer_diversity` (unique counterparties), `beneficiary_churn_rate`, `return_rate` (reversals/chargebacks)

**Structuring / Smurfing**

- Deposit amount heaping below thresholds, ladder patterns, many near-identical amounts from distinct senders.

**Funnel/Pass-through**

- `proportion_out_same_day`, `max_single_counterparty_share`, `graph_in_degree` vs `out_degree imbalance`.

**Graph & Linkage**

- `component_size`, `clustering_coefficient`, `betweenness_centrality`, **edge persistence** (stable relationships vs ephemeral hops).
- Shared identifiers across multiple “businesses” (same director, address, payout).

**Risk Overlays**

- Sanctions/PEP hits; adverse media flags; high-risk MCCs/geos.

**Crypto Hybrid**

- `fiat→crypto→fiat` round-trip time; exposure to flagged on-chain clusters; mixer proximity score.

## 8. Detection Approaches (Rules + ML + Graph)

**Typology Rules (baseline, audit-friendly)**

- Rapid pass-through: `inflow>=$X & outflow>=80% within 24h` with ≥N unique beneficiaries.
- Structuring: ≥K deposits in T days, each within ε of threshold.
- Funnel: ≥M senders → 1 receiver → ≥N new receivers inside T.

**Supervised ML (when labeled events exist)**

- Tree ensembles (tabular features) with cost-sensitive loss (optimize SAR-worthy alerts, not generic accuracy).
- Separate **mule detection** vs **transaction risk** models (account vs payment unit of analysis).

**Unsupervised / Semi-supervised**

- **Isolation Forest / Autoencoders** on flow vectors; seasonal baselines.
- **Graph embeddings (node2vec/GraphSAGE)** + clustering to expose communities.
- **Label propagation** from confirmed cases across edges.

**Hybrid Case Scoring**

- Rule triggers generate the case, ML/graph score the case, analyst reviews with evidence bundle (flows, timelines, graph).

## 9. Labeling & Ground-Truth Challenges (and Mitigations)

**Challenges**

- SAR ≠ guilt confirmation (filed on suspicion; outcomes often unknown).
- Law-enforcement feedback is sparse/slow; many cases never adjudicated.
- Class imbalance extreme; label bias to “obvious” cases.

**Mitigations**

- Use **multi-tier labels**: (confirmed law-enforcement hit, high-confidence internal, SAR-filed, typology-trigger only).
- **Outcome proxies**: account closures, clawbacks, collections failures.
- **Temporal validation**: train on quarters with resolved cases; test on newer cohorts with label delay emulation.
- **Human-in-the-loop**: investigator dispositions feed back into training; calibrate on case-level not just transaction-level.

## 10. Evaluation & Regulatory Fitness

- **Alert quality**: % alerts escalated to SAR, SAR-to-law-enforcement-request rate.
- **Workload efficiency**: alerts per analyst, time-to-disposition, duplicate alert rate.
- **Coverage vs Precision**: typology coverage across products/geos vs false positives.
- **Model governance**: stability, drift, periodic backtesting, explainability artifacts (feature importances, rule rationale).
- **Business KPIs**: loss containment, mule takedown rate, recidivism (re-onboarding), partner/bank relationship health.

## 11. Operational Playbooks

**Onboarding Controls**

- KYB: beneficial ownership checks, business model validation, website/invoice sanity, bank statement verification.
- Risk-tiering: high-risk geos/MCCs require EDD; early payout limits; escrow/holdbacks.

**Transaction Monitoring**

- Real-time velocity/rules; cooling periods for new beneficiaries and first-time large amounts.
- Counterparty trust scoring; beneficiary risk-based holds; pattern-based interdiction.

**Mule Disruption**

- Freeze, Review, Remove: freeze suspicious accounts, create linked-case investigations, remove with evidence.
- Consumer education & romance/investment scam warnings; “Report mule recruitment” channels.

**Crypto Bridges**

- Exchange whitelist/blacklist policies; source-of-funds checks; chain analytics integration; on-/off-ramp limits.

**Case Management & SAR**

- Evidence bundles: flow timelines, counterparties, KYC docs, memo text, graph visuals.
- SAR authoring templates, QA review, timely submission; secure storage/audit trail.

## 12. Dashboards & Investigator Views

- **Heatmaps**: corridor risk, inflow/outflow turnover by geo, high-risk MCCs.
- **Entity graphs**: top components by size/risk; bridge nodes; new component growth.
- **Throughput metrics**: same-day outflow %, beneficiary churn, structuring heaping charts.
- **Alert funnel**: rules → dedup → ML risk score → analyst disposition → SAR.
- **Recidivism**: re-onboard attempts; device/IP reuse after closure.

## 13. Common Pitfalls & How to Avoid

- **Rules explosion & alert fatigue**: consolidate, prioritize, deduplicate alerts by entity/case.
- **Black-box models w/o explainability**: keep typology rationale and feature attributions for audit.
- **Ignoring counterparty risk**: focus on one side only; score both ends and the path.
- **Static thresholds across seasons/geos**: adopt cohort baselines; monitor drift.
- **Siloed fraud vs AML**: merge intel—fraud proceeds feed AML flows; share indicators and graphs.

## 14. Investigator Checklist (Triage)

- Does the account show near-100% pass-through behavior?
- Many small deposits near thresholds over short windows?
- Multiple unrelated senders and rapid beneficiary churn?
- Links to known mules (shared device/IP/beneficiary)?
- Cross-border hops or high-risk corridors without business rationale?
- Round-trips (fiat↔crypto↔fiat) or marketplace payout laundering?
- Is there documentation (invoices, contracts) and does it make sense?

## 15. Key Takeaways

- AML is a controls + analytics + governance problem.
- Mule detection sits at the intersection of fraud, risk, and compliance.
- Build entity resolution & graph pipelines, combine typology rules with ML/embeddings, and maintain evidence-driven, explainable cases.
- Optimize for alert quality and operational efficiency—not just model AUC.
- Continuous feedback loops with Ops and (where possible) law enforcement are essential.

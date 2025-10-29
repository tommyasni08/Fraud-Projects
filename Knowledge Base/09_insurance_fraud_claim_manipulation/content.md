# 📘 Module 9 - Insurance Fraud & Claim Manipulation

## 0 TL;DR

Insurance fraud covers **intentional deception during policy purchase or claim** to obtain undeserved benefits.
It spans **underwriting fraud** (false disclosure), **claim fraud** (exaggeration, staging, duplication), and **provider/insider collusion**.
Modern detection uses **multi-source data fusion** (policy, claims, provider networks, telematics, medical codes), **graph/network analytics, text mining, and hybrid rules + ML + human investigation** pipelines under strict regulatory explainability requirements.

## 1. Definition & Scope

- **Insurance fraud**: Any deliberate misrepresentation causing financial gain to a claimant, provider, or intermediary.
- **Soft fraud**: Exaggeration or opportunistic inflation (e.g., “bump-up” repair bills).
- **Hard fraud**: Planned events (staged accidents, ghost patients, arson).
- **Stakeholders**: Policyholders, claimants, healthcare providers, repair shops, agents, employees.

## 2. Motivations & Incentives

| Actor              | Motivation                                                                 |
| ------------------ | -------------------------------------------------------------------------- |
| Policyholder       | Lower premiums, gain payout, revenge, moral hazard (“I’ve paid for years”) |
| Organized rings    | High ROI, low prosecution risk, ability to recycle identities              |
| Providers          | Upcoding, phantom services, kickbacks                                      |
| Employees / Agents | Commission fraud, ghost policies, data leaks                               |

## 3. Fraud Lifecycle

| Stage                | Fraud Type                    | Example                                                   |
| -------------------- | ----------------------------- | --------------------------------------------------------- |
| **Underwriting**     | Misrepresentation             | Fake occupation, age, health data, mileage; ghost broking |
| **Policy Servicing** | Mid-term manipulation         | Adding coverage after event, document tampering           |
| **Claim Submission** | False or inflated loss        | Staged accident, fake receipts                            |
| **Settlement**       | Collusion or insider override | Adjuster–claimant arrangement, double payouts             |
| **Post-claim**       | Recovery obstruction          | Fake bankruptcy, asset hiding                             |

## 4. Attack Vectors & Typologies

- **Auto**: Staged collisions, jump-ins (add fake passengers), inflated repair estimates, phantom towing.
- **Property**: Serial small fires/thefts, multiple claims for same loss, counterfeit invoices.
- **Health / Medical**: Upcoding CPT codes, billing for unrendered services, phantom clinics.
- **Life**: Fabricated death certificates, identity recycling across countries.
- **Workers’ Comp**: Fake injuries, prolonged recovery with falsified medical certificates.
- **Agent Fraud**: Ghost policies, premium pocketing, fake beneficiaries.

## 5. Real-World Examples

- **U.S. Auto “Crash-for-Cash” Rings (2019–2022)**: Orchestrated collisions involving drivers, passengers, clinics, lawyers.
- **India Health-Insurance Scam (2021)**: Phantom hospitals filing thousands of COVID reimbursements with cloned patient IDs.
- **U.K. Ghost-Broking**: Brokers selling forged policies to drivers—valid-looking but unregistered.

## 6. Business Impact

- **Financial**: Global insurance fraud ≈ > $80 B / year (U.S. FBI est.).
- **Operational**: Higher loss ratios, SIU overload.
- **Pricing**: Honest customers subsidize fraud → churn.
- **Regulatory**: Solvency, consumer-protection violations.
- **Reputational**: Perceived unfairness when false negatives or false positives occur.

## 7. Signals & Data Sources

**Structured Data**

- Policy metadata (tenure, coverage type, declared attributes).
- Claim data (amount, time since policy inception, cause codes).
- Provider data (hospital, garage, doctor, adjuster IDs).
- Payment & bank info, repair invoices, CPT/ICD medical codes.

**Unstructured / External**

- Text notes from adjusters & call logs.
- Photos, videos, EXIF metadata.
- Telematics / IoT: speed, location, impact g-force, trip signatures.
- Social-media cross-validation.

## 8. Feature Engineering

| Dimension              | Example Features                                                                             | Insight                  |
| ---------------------- | -------------------------------------------------------------------------------------------- | ------------------------ |
| **Temporal**           | `claim_lag = event_date - policy_start`; `claim_frequency_12m`                               | Early / frequent claims  |
| **Financial**          | `claim_amount / sum_premium`; outlier vs peer cohort                                         | Disproportionate payouts |
| **Behavioral**         | Same phone/email across multiple policies                                                    | Identity reuse           |
| **Provider**           | `claims_per_provider`, `avg_bill_to_peer_ratio`                                              | Over-billing             |
| **Text / NLP**         | Embedding similarity of claim descriptions; sentiment; key-phrase counts (“sudden”, “minor”) | Template use             |
| **Image / Telematics** | Impact angle mismatch; speed < threshold                                                     | Staged collisions        |
| **Graph / Relational** | `shared_addresses`, `component_size`, `triad_density`                                        | Rings and collusion      |

## 9. Graph & Network Analytics

**Graph Elements**

- **Nodes**: claimants, providers, adjusters, vehicles, addresses, phones, bank accounts.
- **Edges**: co-claims, shared assets, co-payments, phone/device reuse.

**Use-cases**

1. **Ring detection**: Dense components with repeated co-participation.
2. **Provider collusion**: Multiple claimants routed to same clinic/garage.
3. **Identity recycling**: Single individual appears in different roles across policies.
4. **Role ranking**: Degree/betweenness to find coordinators.

**Techniques**: Louvain/Leiden clustering, PageRank, node2vec embeddings + anomaly scoring.

## 10. Labeling Challenges & Mitigations

| Challenge                                 | Mitigation                                           |
| ----------------------------------------- | ---------------------------------------------------- |
| Sparse confirmed fraud (few SIU outcomes) | Semi-supervised / PU learning; label propagation     |
| Investigation lag (months)                | Train on older closed cases; temporal validation     |
| Ambiguous outcomes (partial fraud)        | Multi-label scoring (clean / suspicious / confirmed) |
| Reviewer inconsistency                    | Centralized annotation schema, active learning loops |

## 11. Modeling Approaches

**Rules & Expert Systems**

- Red-flag indicators: early claim, high claim/premium ratio, same provider pattern.
- Business-auditable, fast to deploy.

**Supervised ML**

- Gradient boosting, logistic regression, neural nets on engineered features.
- Cost-sensitive learning weighted by claim amount.

**Unsupervised / Semi-supervised**

- Isolation Forest, autoencoders for rare-pattern detection.
- PU learning on labeled positives + unlabeled pool.

**Graph-based ML**

- Node embeddings → clustering or classification (rings, providers).
- Temporal graphs for evolving fraud rings.

**Text & Image Models**

- NLP for adjuster notes; computer vision for accident-photo inconsistencies.

**Human-in-the-loop**

- ML ranks; SIU analysts validate; feedback retrains model.

## 12. Regulatory & Ethical Constraints

- **Explainability**: Claim denials must be justifiable (GDPR Art. 22, local equivalents).
- **Fairness**: Avoid bias (e.g., postal-code or demographic proxies).
- **Privacy**: Medical & financial data require consent; HIPAA/GDPR controls.
- **Audit trail**: Every model decision → evidence record.
- **Model risk management**: Regular validation, drift checks, governance committee approval.

## 13. KPIs & Dashboards

| Metric                                                  | Purpose                 |
| ------------------------------------------------------- | ----------------------- |
| Fraud detection rate (% confirmed fraud / total claims) | Effectiveness           |
| SIU referral precision & recall                         | Efficiency of triage    |
| Average claim savings ($)                               | Financial ROI           |
| Investigation turnaround time                           | Operational speed       |
| False-positive rate                                     | CX balance              |
| Network growth / cluster recurrence                     | Ring evolution tracking |

## 14. Practical Playbook

**Prevention**

- KYC verification at underwriting; e-policy document controls; cross-check declared data (vehicle, health).

**Early-Warning & Monitoring**

- Velocity rules for early claims; anomaly scoring at FNOL (first notice of loss).
- Link analysis before payout approval.

**Investigation**

- Graph visualizer dashboards for SIU.
- Text analytics to summarize narratives.
- Evidence bundles auto-generated for regulator/legal.

**Feedback**

- Confirmed cases → feature store → retraining.
- Cost-benefit analysis for rule recalibration.

## 15. Investigator Checklist

- Claim filed soon after policy inception?
- Same claimant / address / provider seen in multiple cases?
- Claim photos / telematics consistent with event?
- Billing codes inflated or duplicated?
- Adjuster / provider unusually high approval rate?
- Prior fraud alerts linked via phone, bank, or license plate?

## 16. Key Takeaways

- Insurance fraud = multi-actor ecosystem: claimants, providers, intermediaries, insiders.
- Detection relies on multi-modal data (structured, text, image, graph).
- Combine expert red-flags + ML + graph intelligence with SIU feedback loops.
- Maintain auditability & fairness—critical under insurance regulation.
- Continuous model governance and cross-industry intelligence sharing are essential.

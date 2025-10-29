# 📘 Module 10 - Loan, Credit & BNPL Fraud

## 0 TL;DR

Loan & BNPL fraud exploits credit origination and repayment infrastructure to obtain funds/products with no intention to repay.
Attackers use synthetic identities, income misrepresentation, device/IP farms, and multi-platform parallel borrowing to maximize exposure quickly, then bust-out (default) across lenders.
Detection demands early-lifecycle signals, credit bureau cross-checks, device & identity linkages, and graph-based exposure control — combined with loss forecasting models that evaluate fraud risk + credit risk together.

## 1. Definition & Scope

- **Application Fraud**: False or manipulated information (identity, employment, income) to secure credit approval.
- **Bust-Out Fraud**: Fraudster builds good repayment history, then suddenly maxes out credit across multiple lenders and disappears.
- **BNPL Fraud**: Fast credit at checkout — targets frictionless approval; often ATO + synthetic identity + mule cash-outs.
- **Insider & Merchant Collusion**: Fake merchants approving fraudulent financing transactions.

**Key Concept**:
Credit fraud != credit risk.
Credit fraud = intentional deception from day 1.

## 2. Motivations & Fraud Economics

| Motivation                     | How attackers profit                                                |
| ------------------------------ | ------------------------------------------------------------------- |
| **Fast cash**                  | Loan payout → mule transfers                                        |
| **Goods laundering**           | BNPL purchases → resell electronics                                 |
| **Credit arbitrage**           | Apply across many lenders before bureaus update (“credit shopping”) |
| **Synthetic identity scaling** | Many fake borrowers with no victim complaints                       |
| **Asymmetric risk**            | Lender bears default loss, attacker risks low                       |

BNPL is especially vulnerable because identity trust is low (email/phone onboarding) and approval latency is near zero.

## 3. Attack Vectors & TTPs

- **Identity Manipulation**: Synthetic IDs, stolen PII, fake documents.
- **Income / Employment Fraud**: Forged payslips, fake employer calls, manipulated bank statements.
- **Device/IP Masking**: VPNs, emulators to scale onboarding.
- **Merchant Collusion**: Fake stores submit BNPL orders → payout to fraud ring.
- **Multi-Lender Velocity**: Submit simultaneous applications before credit bureau reflects exposure.
- **Repayment Manipulation**: Partial early repayments to raise limits → max-out → ghost.

  Bust-out = trust farming → fraud harvest.

## 4. Industry Examples

- **US & EU BNPL providers**: spikes in synthetic identity approvals → electronics reselling → first payment default (FDP).
- **Asia Fintech Lenders**: loan stacking via agent collusion in rural areas — identical bank accounts across borrowers.
- **App-based installment plans**: device farms mass-apply; early payments used to raise credit tiers, then bust-out.

## 5. Business Impact

- **Direct credit losses**: No recovery; high charge-off.
- **Regulatory & underwriting pressure**: Capital reserve increases, cost of funds worsens.
- **Model corrosion**: Fraudulent good repayment history pollutes PD (Probability of Default) models.
- **Operational**: collections waste, dispute handling.
- **Reputation**: BNPL criticized for “unsafe lending” → trust erosion.

## 6. Signals & Data to Capture

**At Application**

- Email/phone age, device fingerprint, IP risk, KYC quality.
- Identity verification (OCR, face-match, liveness).
- Bank statement ingestion (real income? inflows/outflows profile?).
- Employment verification (digital payroll APIs if available).

**Post-Approval Behavior**

- Repayment timeliness, device reuse across accounts, spending velocity.
- Transaction type: high-liquid resale goods (phones, gaming consoles).

**Cross-Entity / Bureau**

- Hit rate on bureau; recent credit enquiries (credit shopping).
- Shared addresses/phones/employers across many borrowers.

**Merchant / Channel**

- Merchant chargeback & refund patterns.
- High-risk MCC (electronics, jewelry).

## 7. Feature Engineering (High-Signal Examples)

| Category                 | Example Features                                                    | Insight                        |
| ------------------------ | ------------------------------------------------------------------- | ------------------------------ |
| Identity Trust           | `device_per_identity_count`, disposable email flag                  | Synthetic or scaled identities |
| Financial Reality        | `income_to_spend_ratio`, inflow consistency, `salary_day_alignment` | False income claims            |
| Velocity                 | `applications_per_device_24h`, simultaneous lender hits             | Fraud ring velocity            |
| Credit Builder vs Buster | `repayments_before_limit_increase`, `repayment_amount_variance`     | Trust farming then max out     |
| Merchant Risk            | shared payout bank accounts, BNPL refund loop                       | Collusion                      |
| Graph                    | centrality in identity graph; component size across KYC attributes  | Fraud ring networks            |

## 8. Graph & Exposure Control

**Graph Construction**

- Nodes: borrowers, devices, bank accounts, addresses, employers, merchants.
- Edges: applications, orders, payouts, contacts.

**Risk Signals**

- Multiple borrowers → one salary bank account.
- Same device fingerprint with many identities.
- Rapid exposure expansion inside one cluster.

**Exposure Control Actions**

- Lower limits for cluster, or freeze increases until clean repayment over time.

## 9. Labeling Challenges & Mitigations

**Why it’s hard**

- Default ≠ fraud — some users truly cannot repay (credit risk).
- Fraud may appear as good for months (trust-farming).
- Real fraud confirmed only after collections exhaustion.

**Mitigations**

- Tiered labels:
  - Fraud-default (bad intent) vs
  - Credit-default (ability problem)
- Combine signals: identity anomalies + velocity + resale behavior + cluster membership.
- Collections outcomes: “unable to contact”, fake addresses → high fraud likelihood.
- Temporal windows: label older loans only once final status is known.

## 10. Modeling Approaches

**Rules & Configurable Underwriting**

- Minimum identity quality checks (KYC, device history).
- Merchant risk scoring for BNPL.

**Supervised ML**

- GBDT models scoring early fraud probability separate from PD.
- Dual-model architecture:
  - Fraud-at-origination (F1 focus)
  - Loss forecasting (expected loss → LGD × PD)

**Unsupervised / Semi-supervised**

- Isolation Forest on application vectors; find low-density points.
- Graph embeddings → cluster anomaly scoring.

**Sequence / Survival Analysis**

- Time-to-first-default for bust-out detection.
- Hidden Markov Models for repayment transitions.

## 11. Evaluation & Business Tradeoffs

| Metric                                | Meaning                          | Balanced Against                  |
| ------------------------------------- | -------------------------------- | --------------------------------- |
| Fraud Default Rate (FDR)              | % of defaults with fraud signals | Opportunity loss (approvals drop) |
| First Payment Default (FPD)           | Default after first cycle        | Conversion & CX                   |
| Loss Rate & Exposure at Default (EAD) | P&L risk                         | Growth objectives                 |
| Approval Rate                         | Acquisition health               | Risk appetite                     |
| Limit Increase Approval               | LTV expansion                    | Bust-out exposure                 |

Decision Economics:
Approve if EV(repayment) > EV(loss) considering fraud penalty.

## 12. Operational Playbooks

**Onboarding**

- Tiered credit granting; hard KYC for high limits.
- Device fingerprint dedup before approval.
- Limit “no-cost EMI” for risky merchants.

**Exposure Ramp-Up**

- Progressive credit limits tied to genuine repayment behavior.
- Payout holds for BNPL merchants until dispute window clears.

**Post-Approval Monitoring**

- Real-time watch for spike spend velocity + high-liquid SKU mix.
- Freeze further spend after suspicious early payments.

**Collections & Recovery**

- Fraud segmentation: prioritize true credit-risk recovery vs fraud write-off.
- Shared intel with bureaus & networks.

## 13. Dashboards & Analyst Toolkit

- Exposure by risk cohort (device/IP clusters).
- FPD % by merchant/product/geography — BNPL hotspot map.
- Applications per device/IP/email/day → ring formation.
- Repayment curve shifts: DPD (days past due) trajectories.
- Cycle-to-cycle limit increase outcomes (good vs bust behaviors).

## 14. Common Pitfalls & How to Avoid

| Pitfall                                          | Fix                                              |
| ------------------------------------------------ | ------------------------------------------------ |
| Treating fraud as pure credit risk               | Separate models + identity & device signals      |
| Aggressive blocking at underwriting kills growth | Progressive trust with risk monitoring           |
| Ignoring merchant/seller collusion in BNPL       | Merchant risk scoring + payout controls          |
| One-time dedup only                              | Continuous **graph-based exposure refresh**      |
| Labels based only on defaults                    | Incorporate fraud evidence + cluster propagation |

## 15. Investigator Checklist

- Device/IP reused across many “borrowers”?
- Salary deposits vs declared income mismatch?
- Rapid max-out after limit increase?
- Loan stacking / multi-lender app velocity?
- High-liquidity purchase pattern (phones, gold)?
- Default exit strategy: contact unreachable, fake address?
- Merchant payout to same beneficiary seen in fraud ring?

## 16. Key Takeaways

- Loan & BNPL fraud mimics strong credit behavior → detection must start at origination + during early cycles.
- Bust-out = trust farming → exposure grab → disappear.
- Device + identity + merchant graph is more predictive than credit metrics alone.
- Evaluate decisions via expected value, balancing growth and safety.
- Continuous monitoring and feedback loops are critical for catching evolving rings.

# 📘 Module 3 - Payment Fraud (Cards, Wallets & Chargebacks)

## 0 TL;DR

Payment fraud spans **card-present (CP)**, **card-not-present (CNP)**, and **digital-wallet** rails. Attackers monetize via **instant cash-out**, **goods arbitrage**, or **laundering** through **mules/merchants**. Detection requires **multi-layer signals** (transaction, device, network, identity, merchant context), **velocty + graph feature**, **label-lage aware modeling** and **risk-based authorization** that balances **catch rate vs conversion**.

## 1. Definition & Scope

- **Payment fraud**: Unauthorized or deceptive transactions intended to extract value or move illicit funds.
- **CP (Card-Present)**: Physical card at POS. Vectors: skimming, shimming, counterfeit magstripe, stolen cards, merchant collusion.
- **CNP (Card-Not-Present)**: Remote/e-commerce. Vectors: credential stuffing on stored cards, BIN attacks, card testing, phising.
- **Digital wallets & A2A (P2P, RTP)**: Fast rails; vectors: ATO cash-out, social engineering, QR scams, instant transfer abuse.
- **Merchant fraud**: First-party (friendly fraud/chargebacks), collusive merchants, refund/return abuse, synthetic merchants.

## 2. Attacker Motivations (Payoff Models)

- **Immediate cash-out**: High-value eletronics, gift cards, crypto off-ramps, ATM withdrawals (CP).
- **Arbitrage**: Resell physical/digital goods; exploit cross-border price gaps.
- **Infrastructure**: "Warm-up" cards via small approvals; create **mule networks** for laundering.
- **Promo leakage**: Voucher stacking, feake refunds to external instruments.
- **Asymmetric risk**: Instant funds to attacker vs weeks-long chargeback cycle for victims/mechants.

## 3. Common Attack Vectors & TTPs

- **Data compromise**: Phising, malware, merchant breaches, form-jacking (JS sniffers).
- **Card testing/BIN attacks**: Scripted micro-auths to find live PAN+CVV; ramp to larger purchases.
- **ATO-driven spend**: Take over wallet/account -> change payout, add payee, drain funds.
- **Synthetic cards/identities**: Engineered profiles to pass KYC + build credit -> bust-out.
- **Merchant collusion**: Fake orders, refund to alternate instruments, split payouts to mules.
- **Refund & disputes gaming**: Friendly fraud, INR claims, double refunds (payment + out-of-band)

## 4. Illustrative INdusstry Examples (Patterns to recognize)

- **Banking/Fintech**: CNP spikes after a major breach -> card testing at low-risk digital MCCs, then luxury spend.
- **E-commerce/Ride-hailing**: Burst of failed CVV -> followed by thin approvals; new accounts + voucher use + instant refund claims; repeated device/IP across "different" customers.
- **P2P Wallets**: ATO -> beneficiary added -> step-up bypass via SIM swap -> rapid series of transfers to fresh accounts.

## 5. Business Impact

- **Financial**: Chargebacks, refunds, interchange losses, network/aquirer fines.
- **Conversion**: Over-aggresive controls lower auth rates and GMV.
- **Compliance**: PCI-DSS, PSD2/SCA, MAS/FFIEC expectations for risk controls.
- **Ops cost**: Disputes handling, manual reviews, collections.
- **Reputation & trust**: Customer churn after visible fraud events.

## 6. Signals to Capture (Raw & Enriched)

**Transactions**

- Acmount, currency, MCC, merchant ID, channel (CP,CNP,in-app), AVS/CVV result, 3DS result, issuer response codes, recurring vs one-off, first-time vs repeat merchant.

**Identity & Account**

- Account age, KYC tier, prior disputes, payment instrument age (days since added), recent profile changes (email/phone/payout).

**Device & Network**

- Device fingerprint (ID stability, jailbreak/root, emulator flags), user-agent, IP/ASN risk (datacenter/VPN/TOR), geo vs billing country, latency/JIT jitter patterns.

**Behavioral**

- Time-to-purchase after login/add-card, checkout speed, cart edit frequency, night-hour bias, session clickstream anomalies.

**Payment rail enrichments**

- BIN/IIN metadata (issuer country, prepaid/debit/credit), risk tiers by BIN, historical decline/chargeback rates by BIN/MCC.

**Merchant context**

- Merchant tenure, dispute rate, refund policy leniency, payout instrument reuse across "different" merchants.

**Graph/Linkage**

- Device/IP/phone/email shared across accounts; beneficiary/payour reuse; repeated buyer <-> merchant edges.

## 7. Feature Engineering (High-Signal Examples)

**Velocty & Recency**

- `txn_count_5m/1h/24h`, `sum_amount_24h`, `unique_merchant_count_24h`, `fail_to_approve_ratio_1h`, `cvv_fail_streak`.

**Deviation from Baselines**

- Z-score of amount vs user baseline; AOV deviation vs peer cohort; distance from typical geo/time window.

**Rail-spefici**

- `time_since_card_added` (fresh card risk), `3DS_result * issuer_behavior`, `avs_match_flag`, `mcc_risk_score`.

**Cross-entity/Graph**

- `accounts_per_device`, `devices_per_account`, `payout_accounts_shared_count`, `buyer_merchant_repeat_edge_rate`.

**Testing fingerprints**

- Small-amount approvals preceding large purchase; sequential amount laddering; multiple cards testing from one device.

**ATO composites**

- New device + impossible travel + payout change + high-value transfer within X minutes.

## 8. Labeling Challenges (and Workarounds)

- **Chargeback lag**: 30-90 days; labels arrive late and may be biased by issuer decisions.
- **Ambiquity**: Friendly fraud vs true fraud; merchant abuse disguised as cutomer dispute.
- **Selection bias**: Reviewed/charged back transactions != full population.

**Mitigations**

- **Proxy/weak labels**: Short-window confirmations (issuer hotlists, confirmed ATO, manual cause outcomes).
- **Outcome stacking**: Combine dispute reasons codes, network alerts, recovery status.
- **Temporal handling**: Train on older windows, validate on newer; simulate label delay.
- **Cost-sensitive learning**: Weight positives by $loss; optimize business utility, not accuracy.

## 9. Modeling Approaches (Online + Batch)

**Rules & Policies (baseline)**

- Allow/deny lists, geofences, MCC caps, velocity rules, card-testing patterns, ATO sequences.

**Supervised ML (real-time scoring)**

- **Tree ensembles (XGBoost/LightGBM)**: Strong on tabular, fast to score.
- **Logistic regression**: Calibrated risk scores, easier to explain to networks/regulators.
- **Neural nets**: Session or sequence models in high-volume settings.

**Unsupervised/Semi-supervised**

- Isolation Forest/autoencoders for new-pattern detection, especially card testing and novel mules.
- **Graph ML**: Node2vec/ GraphSAGE to detect collusion rings, buyer-merchant loops, mule webs.

**Hybrid Risk Scoring**

- Rules for obvious patterns -> short-circuit blocks.
- ML scores -> risk-based orchestration:
  - Low risk: straight-through approval.
  - Medium risk: 3DS/step-up/OTP.
  - High: decline/hold/manual review.

**Drift & Online Learning**

- Monitor approvals, issuer declines, chargebacks by cohort; retrain with rolling windows; champion-challenger.

## 10. Evaluation & Trade-offs (Fraud vs Conversion)

**Model metrics**

- Precision/Recall/F1;ROC-UAC; PR-AUC(imbalance); calibration (Brier score).

**Business KPIs**

- **Fraud Loss % GMW** (leakage), **chargeback rate**, auth approval rate, issuer soft/hard declines, manual review rate, step-up completion rate, false-positive cost, time-to-decision.

**Decision economics**

- Expected Value per decision:
  `EV = (approve_value x P(good)) - (fraud_cost x P(fraud)) - (friction_cost x 1[step-out])`
- Tune thresholds and step-up policies to maximze **net EV**; A/B test **safety-conversion frontier**.

## 11. Practical Playbooks (What teams actually do)

**Card Testing Containment**

- Real-time detection of many small auths per device/IP/BIN; throttle or block; scrub leaked BINs; raised min auth amounts for risky cohorts.

**ATO Cash-out Guardrails**

- Step-up on new device + beneficiary change + transfer; timebox new payee limites; cooling-off periods for payout edits.

**3DS/SCA Orchestration**

- Adaptive 3DS: invoke based on dynamic risk; log issuer-specific behaviors to avoid conversion cliffs.

**Merchant Risk**

- KYB strength; monitor dispute ratios; refund-to-sale anomalies; shared payout accounts across "different" merchants; rolling reserved for new/high-risk merchants.

**Chargeback Ops**

- Reason-code analytics; representment kits with device/3DS/AVS evidence; close-loop back to features.

**Consortium & Signals**

- Network hotlists, compromised card feeds, device reputation networks; feed into pre-auth risk.

## 12. Common Pitfalls & How to Avoid

- **Overfitting yesterday's fraud**: Maintain unsupervised detectors; rotate rules; red-team new vectors.
- **Friction overkill**: Blanket 3DS kill conversion; use **adaptive triggers**.
- **Ignoring issuer heterogeneity**: Some issuers decline aggresively; cohort models per BIN/issuer/country help.
- **One-sided focus**: Buyer risk only; ignore **merchant collusion** and **mule networks**.
- **Static thresholds**: Seasonality, promos, and holidays demand adaptive baseliness.

## 13. Starter Dashboards (Analyst View)

- **Auth funnel**: attemps -> approved -> 3DS invoked -> 3DS pass -> settled -> disputed.
- **Leakage**: fraud loss % GMV, chargeback rate by MCC/issuer/BIN/country.
- **Card testing**: CVV fail rate, micro-auth spikes by ASN/IP tile.
- **ATO cash-out**: payout edits -> transfer attempts -> step-up success -> confirmed fraud.
- **Merchant health**: disupute/refund ratios, payout holds, shared payout accounts.
- **Model health**: score drift, PSI, precision/recall by cohort, appeal overturns.

## 14. Investigator Checklist

- Is this **new card/new device/new payee**? How fast to high-value transactions ?
- BIN/issuer/country mismatches? AVS/CVV/3DS results?
- Shared **device/IP/beneficiary** with prior fraud?
- Prior **micro-auths** before big ticket?
- Merchant dispute/refund history abnormal?
- Evidence for representment: device fingerprint, 3DS cryptogram, IP, geo, session trail.

## 15. Key Takeaways

- Payment fraud is **speed + scale**. Your defense is **signal depth**, **risk-based orchestration**, and **fast feedback loop**.
- Blend **rules + supervised ML + unsupervised/graph** to catch both known and novel patterns.
- Optimize **net EV**, not just precision/recall - balance **fraud catch** with **user conversion** and **issuer quirks**.

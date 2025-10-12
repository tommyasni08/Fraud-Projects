# 📘 Module 4 - Promo Abuse & Incentive Gaming

## 0 TL;DR

Promo abuse happens when users (or rings) **exploit marketing incentives** --coupons, referrals, sign-up bonuses, free shipping/credits, surge/quest bonuses -- **wihtout genuine intent to transact long-term**. It spans **multi-accounting, device/IP farms, collusion, referral loops, refund stacking, and code leaks**. Winning requires **progressive trust, identity & device deduplication, graph detection of loops, promo governance,** and **joint ownership** with Growth/Marketing so you reduce leakage **without killing conversion**.

## 1. Definition & Scope

- **Promo abuse/incentive gaming**: Systematic exploitation of promotional value (vouchers, credits, referral cash, fee waivers, driver/merchant incentives) **contrary to policy intent**.
- **Not**: normal coupon usage, price discrimination tests, or A/B marketing variance.
- **Where it appears**: e-commerce, food/grocery delivery, ride-hailing, subscription apps, fintech signup bonuses, wallets, BNPL, social "invite-a-friend."

## 2. Attacker Motivations

- **Direct cash-outs**: Referral cash or wallet credits -> withdraw or convert via mules.
- **Goods arbitrage**: Stack coupons/free shipping to aqcuire goods cheaply -> resell.
- **Incentive harvesting**: Driver/courier/merchant bonuses engineered via collusions.
- **At-scale farming**: Device/SIM farms create thousands of "new users" to drain promo budgets.
- **Asymmetric risk**: Low penalty if caught; promos are designed to be easy -> low friction, fast payout.

## 3. Common Attack Vectors & TTPs

- **Multi-accounting**: Disposable emails/VOIP; re-use of devices/IPs; emulator farms.
- **Referral loops**: Self-referral chains, rings exchanging invites, synthetic family trees.
- **Code leakge**: Private codes leaked to forums/Telegram; brute-forced voucher IDs.
- **Refund stacking**: "item not received" or partial refunds combined with promo credits.
- **Collusion**: Buyer-seller (or rider-driver-merchant) coordinate orders to farm incentives.
- **Geo & time gaming**: Sign-ups or orders spiking exactly at campaign start windows; hotspot exploitation.

## 4.Illustrative Industry Examples (Patterns)

- **E-commerce/food delivery**: Thousands of "new" accounts from the same device/IP tile redeeming first-order free delivery + voucher stack; refunds routed to the same payout account.
- **Ride-hailing**: Driver-rider collusion to trigger streak/quest bonuses via short, cancel-and-re-book loops.
- **Fintecth/wallet**: Signup-bonus farms using synthetic identities; cash-out via P2P to mule accounts;
- **Social apps**: Invite-bonus pyramids-same device seeding dozens of "new users" who never activate beyond day-1.

## 5. Business Impact

- **Marketing ROI dilution**: CAC looks great; LTV collapse (zombie accounts).
- **Fraud budget leakge**: Promo spend behaves like cash; direct P&L impact.
- **Data pollution**: Inflated MAU/DAU/"new users" -> bad strategy decisions.
- **Marketplace health**: Incentive gaming distorts pricing/availability (e.g. surge manipulation).
- **Reputation & trust**: Legit users perceive unfairness; partner lose confidence.

## 6. Signals to Capture (Raw & Enriched)

**Account & Identity**

- Account age, KYC tier, name/email/phone patterns (disposable domains, VOIP).
- Payment instrument age; card/wallet reuse across "different" accounts.

**Device & Network**

- Device fingerprint (stability, emulator/root flags), sensor presence.
- IP/ASN risk (datacenter/VPN/TOR), geolocation tiles, Wi-Fi/cell twoer consistency.

**Promo & Campaign Context**

- Voucher code type (public/private/single-use), issue channel, intended audience.
- Time since campaign launch; redemption window; code provenance (leaked vs targeted).

**Behavioral**

- First-order composition (promo-eligible SKUs only), cart edit velocity, checkout speed.
- Post-redeem behavior (does user return without promo?).

**Transaction/Operational**

- Refund/INR frequency, partial vs full refunds, courier/driver acceptance/cancel rhytms.
- Payout instruments for sellers/mechants; shared bank accounts.

**Graph/Linkage**

- Shared device/IP/phone/email/address/payout; referral edges (who invited whom).
- Buyer <-> seller repetition rates; driver <-> rider loops; cluster density.

## 7. Feature Engineering (High-Signal Examples)

**Velocity & Regency**

- `redemptions_per_device_24h`,`new_accounts_per_IP_1h`, `unique_payment_instruments_per_device_7d`.
- `time_since_account_creation_to_first_redeem`.

**Promo-speficic**

- `promo_to_gmw_ratio` per user/cohort; `stack_count` per order; `avg_discount_pct`.
- `first_order_net_value` (AOV minus voucher/credits); min order thresholds hit exactly.

**Identity & Device Dedup**

- `accounts_per_device`, `device_per_account`, `accounts_per_phone/email/card`.
- Entropy measures for email/phone patterns; similarity of names/addressed.

**Referral Graph**

- `avg_referrals_per_node`, `cycle_length` (self-loops), `component_size` growth rate.
- Depth-first "family trees" with low activation beyond Day-1.

**Collusion & Ops**

- Repeated buyer <-> seller pairs; triad density for rider-driver-merchant.
- `refund_rate_after_promo` spike; `payout_account_shared_count` across merchants.

## 8. Graph Angle (How to See the Rings)

- Build graphs where **nodes** = users/drivers/merchants/devices/payouts and **edges** = referrals, transactions, shared attributes.
- Use **community detection** to spot dense clusters of "new users" redeeming in bursts.
- Identify **bridge nodes** (mules) via betweenness centrality connecting clusters to payouts.
- Detect **referral cycles/triangles**; measure **component growth** aligned with campaign start.
- Output **cluter risk scores** + evidence bundles for Ops (shared device/IP, timeline, code usage).

## 9. Labeling Challenges (and Mitigations)

**Challenges**

- **Ambiguity**: Opportunistic bargain-hunters vs policy-violicting abuse.
- **Lagging truth**: Real LTV takes months; early labels are weak.
- **Selection bias**: Only investigated cohorts labeled; overrepresents obvious cases.

**Mitigations**

- **Policy tags**: Define "abuse" vs "Heave promo use" clearly; label by **rule of intent + duplication evidence**.
- **Weak labels**: Combine signals (duplication counts, graph membership, refund after redeem, zero post-promo activity).
- **A/B test outcomes**: Downstream behaviour after friction/limits servers a quasi-ground truth.
- **Semi-supervised**: Cluster suspicious cohorts; propogate labels from a small reviewed seed.
- **Business overlays**: Require activation milestones (N orders, non-promo purchase) before counting as "good acquisition".

## 10. Modeling Approaches

**Rules & Policies**

- Single-use enforcement; per-device/phone/card caps; referral eligibility rules (no self-referrals, cool-downs).
- Campaign-time throttles; geo/ASN allowlists/denylists.

**Supervised ML**

- Tree ensembles on tabular signals (duplication counts, promo rations, velicty, graph features).
- Cost-sensitive loss-optimize for **promo leakage reduction**, not generic accuracy.

**Un/Semi-supervised**

- Isolation Forest/autoencoders for novel abuse waves.
- Graph clustering/embeddings (node2vec/GraphSAGE) for loops and collusion.

**Hybrid Risk Orchestration**

- **Low risk**: frictionless redeem.
- **Medium**: step-up (phone/SMS verify, card bind, address verify).
- **High**: decline, manual review, or require **activation proof** (non-promo transaction).

## 11. Governance & Trade-offs with Growth/Marketing

- **Shared KPIs**: Optimize **Net Good Users (NGU)** and **Promo ROI**, not raw signups.
- **Progressive trust**: Unlock richer promos after clean behavior milestones.
- **Frequency caps & tiering**: Per device/phone/card/ASN; per-city tile.
- **Targeting discipline**: Tight audience lists; crpytographically strong single-use codes; short validity windows.
- **Post-compaign retros**: Measure **leakge %**, **post-promo retention**, **refund after redeem**, **collusion cluster size**.

## 12. Practical Playbooks

**Before campaign**

- Risk review of mechanics; simulate abuse scenarios; set rate limits and code strength.
- Seed allowlists for trusted cohorts; set exemptions carefully.

**During campaign**

- Real-time dashboards: redemptions per device/IP/ASN, referral graph growth, refund after redeem.
- Throttle triggers: burst redemption per tile/ASN; sudden device reuse spikes.

**After compaign**

- Attribution sanity checks: NGU, Day-7/30 retention without promos.
- Cluster audits. top risky components -> payout holds, KYB re-checks, deactivation with appeals path.

## 13. Dashboards & KPIs (Analyst View)

- **Promo ROI**: (incremental GMW - promo spend - fraud/refund leakage) / promo spend.
- **Leakge rate**: % of promo redeemed by accounts later flagged (dup/graph/refund).
- **Dup signals**: accounts per device/phone/card/IP; referral loops/cycles.
- **Retentions**: % users with non-promo order by Day-7/30.
- **Appeals/FP**: overturn rate for blocker redemptions (guard against over-blocking).

## 14. Common Pitfalls & How to Avoid

- **Over-friction**: Killing conversion with blanket KYC/OTP.
  - Use **risk-based** step-ups; unlock with milestons.
- **Weak code design**: Reusable/public codes, long validity windows.
  - Use single-use, scoped, short-lived codes; bind to identity.
- **Promo owned only by Marketing**: No join guardrails.
  - **Fraud + Growth** co-own targeting, caps, and success metrics.
- **ignoring supply-side incentives**: Driver/merchant collusion leaks incentives.
  - KYB, payout dedup, quest/streak anti-gaming checks.
- **Static thresholds**: Attackers adapt to caps.
  - Rotate limits, randomize checks, monitor by cohort/ASN/tile.

## 15. Investigator Checklist (Triage)

- Do "different" account share **device/IP/phone/card/address/payout?**
- is **referral tree** dominated by a few seed devices? Any cycles/triangles?
- Promo used **immediately after signup** with zero follow-on activity ?
- **Refund after redeem** pattern? Same riders/buyers with same drivers/merchants?
- Codes from **leak sources** vs targeted distribution ?

## 16. Key Takeaways

- Treat promotions like **cash** with an **access control and risk policy**.
- Combine **deduplication, graph intelligence, and risk-based orchestration** to cut leakage.
- Align with Growth on **Net Good Users and post-promot retention**, not vanity sign-ups.

# 📘 Module 2 - Synthetic Identity & Onboarding Fraud

## 0 TL;DR

**Synthetic identity fraud (SIF)** = creating a new "person" by blending **real** identifiers (e.g., national ID fragments, DOB, phone) with **fabricated** data (name, address, documents). Unlike stolen-identity ATO, there's **no real victim** to complain, so fraud can "age" undetected and **bust out** later (loans, credit lines, promo cash-outs). Detection relies on **entity resolution, duplication signals, graph analysis, and document/biometric integtrity** at onboarding.

## 1. Definition

- **Synthetic Identity Fraud**: Creation of accounts using partial legitimate data + fabricated attributes to pass onboarding/KYC and build history for later abuse.

- **Differ from**:
  - **Stolen Identity Fraud**: Entirely impersonates a real person; victims report quickly.
  - **New account Fraud (NAF)**: Any fraudulent new account; SIF is a subset optimized to look **legitimate** and persist.

## 2. Attacker Motivations (Cross-Industry)

- **Credit building & burst-out (banks/fintecht)**: Open accounts, behave normally, then max out cards/loans and disappear.
- **Cash-out infrastructure (all)**: Use synthetic accounts as "clean" intermediaries to launder proceeds.
- **Promo/referral farming (e-commerce, delivery, social)**: Farm "new user" incentives, vouchers, shipping credits.
- **Resillience & scale**: No real victim noise -> safer to operate long-term, easier to industrialize.

## 3. Attack Vectors & TTPs (Tactics, Techniques, and Procedures)

- **Data Assembly**: Breach dumps, data brokers, phising to gather high-value fragments (IDs, DOBs, phone).
- **Document forgery**: Tampered IDs, template overlays, synthetic faces; low-grade print/scan artifacts.
- **Device/SIM farms**: OTP receipt, multi-account registration, IP rotation (VPN, proxies).
- **Mule recruitment**: Willing sellers of identity or bank accounts to anchor synthetic personas.
- **Aging strategy**: Small, normal activity to accumulate trust; later **burst-out** or promo harvesting.

## 4. Illustrative Case Studies

- **US bank fraud rings**: Fabricated personas + shell companies to open credit lines and steal ~$1-2M per ring before takedown (typical pattern: months of aging, sudden burst-out).
- **Marketplace/delivery promo rings (SE Asia & US)**:Thousands of "new" accounts from device farms to exploit sign-up vouchers, free shipping, and referral loops; payouts routed to common bank accounts.

(Focus is on patterns you'll see repeatedly, not specific news citations.)

## 5. Business Impact

- **Financial**: Credit losses, promo leakage, refunds, colletions costs.
- **Regulatory/Compliance**:KYC/AML breaches, fines, remeditation mandates (especially in banking).
- **Operational**: Corrupted growth metrics (fake "new users"), polluted datasets, manual review burden.
- **Trust/Reputation**: Partners/advertisers question user quality; banks face regulator scrutiny.

## 6. Onboarding/KTC Signals to Inspect (Analyst Checklist)

**Personal/Identity**

- Name, DOB, national ID/passport, issuing country
- Consistency checks (DOB <-> age; document number format validity)

**Contact & Address**

- Phone (carrier type/VOIP, tenure, porting history), email (disposable domain?), address (geocoding quality)

**Document & Biometric**

- Image forensics (font/hologram parity, MRZ/QR consistency), selfie liveness, face-match scores, replay/spoof indicators

**Device & Network**

- Device fingerprint (hardware/OS, jailbreak/root flags), emualator hints, IP/ASN risk (datacenter, VPN, TOR), geo at sign-up

**Behavioral**

- Form-fill timing (copy/paste bursts), field edits frequency, typing cadence irregularities

**Temporal/Cohort**

- Sign-up bursts by tile/ASN/device, sudden spikes coinciding with new promo campaigns

## 7. Feature Engineering (Derived Features That Matter)

**Duplication/Reuse**

- #accounts sharing same phone/email/device/IP/address/bank account
- #unique identifiers per device/IP (device centricity)

**Geospatial & Address Quality**

- Address geocode confidence; many "different" users resolved to the same building/unit
- Distance to known synthetic clusters; PO boxes & freight forwarders

**String & Identity Similarity**

- Name variants (Jaro-Winkler/Levenshteion); DOB day/month swaps; transliteration patterns

**Velocity & Rhythm**

- Sign-ups per device/IP per hour; time-since-last-signup on same device; campaign-hour spikes

**Document/Face Integrity**

- MRZ checksum parity; font alignment; phoot quality histograms; selfie-ID face embedding distance; liveness challenge success ratio

**Entropy & Diversity**

- Unnatural uniformity (too many 01-Jan DOBs, same email pattern); or over-randomization (noise injection in device/browser)

# 8. Graph Angle (How to Catch Rings)

- **Build an identity graph**: nodes = accounts; edges= shared attributes (phone, email, device, IP, address, payout).
- **Look for**:
  - **Dense communities** (community detection; high clustering coefficients)
  - **Bridge nodes** (mules) with highe betweenness centrality connecting clusters
  - **Start patterns** (one device spawning many identities)
  - **Component growth** over time (new synthetics attaching to old cores)
- **Outputs for Ops**: cluter risk scores, evidence bundles (shared attributes, timelines, map tiles), payout holds.

# 9. Labeling Challenges (and Mitigations)

- **No victim complaints**: synthetics don't self-report.
- **Label latency**: months of "good" behavior before bust-out.
- **Selection bias**: investigators label obvious cases; subtle rings stay unlabeled.
- **Privacy/consent constraints**: hard to share identity ground truth across institutions.
  **Mitigations**
- Semi-supervised learning; human-in-the-loop triage
- Weak labels (collections outcomes, KYB rejections, charge-off cohorts)
- Graph-propagated labels (seed a few confirmed nodes, spread suspicion via edges)
- Synthetic positives (programmatic test identifiers for calibration)

# 10. Modeling Approaches & What to Prioritize

**When labels are available (supervised)**

- **Tree ensembles (XGBoost/LightGBM)**: strong on tabular identity features
- **Stacked meta-models**: blend document/biometric scores + duplication/graph features + velocity
- **Cost-sensitive training**: reflect fraud/FP business costs
  **When labels are sparse (unsupervised/semi-supervised)**
- **Isolation Forest/Autoencoders**: anomaly scores on identity vectors
- **Graph embeddings + clustering**: node2vec/DeepWalk for community discovery
- **Rule-augmented scoring**: obvious red flags (e.g., 1 device -> 10 "new users" in 30 min)
  **High-value features to prioritze**
- Cross-entity reuse counts (phone/email/device/IP/address/payout)
- Face-match & liveness failure patterns; document forensics flags
- Address geocode clustering; freight-forwarder/PO-box heuristics
- Temporal spikes around promos (sign-up cadence, referral triangles)
- Graph centrality and community membership features

# 11. Evaluation & Business Guardrails

- **Model metics**: Precision/Recall/F1,ROC-UAC; **PR-AUC** often more informative under class imbalance
- **Business KPIs**: Fraud loss % of GMV/loans, promo leakage %, FP appeal overturn rate, manual review SLA
- **Safety-Friction frontier**: tiered KYC (progressive trust); A/B test frictions vs conversion/approval rates

# 12. Practical Playbooks

**Onboarding**

- Risk-based KYC: start light -> step up on risk (doc + selfie + liveness)
- Disposable email/VOIP screening; phone tenure; address validation & geocoding
- Device/IP reputation; emulator/root blocks where applicable
  **Entity Resolution**
- Real-time duplicate checks across phone/email/device/IP/address/payout
- Maintain **watchlists** for high-risk attributes/tiles/ASNs
  **Graph Ops**
- Batch & streaming pipelines to maintain identity graphs
- Payout holds and KYB re-verification for suspicious communities
- Evidence packs for investigators (shared attributes, timelines, maps, images)

**Promo Governance**

- Cap promos for low-trust accounts; referral cool-downs; per-device/ASN limits
- Retros on promo campaigns to quantify leakage & tigthen rules

# 13. Common Pitfalls & How to Avoid Them

- **Over-reliance on KYC vendor scores**: enrich with your duplication + graph + velocty features.
- **Blocking too early**: use progressive trust - don't nuke conversion for honest new users
- **Siloed fraud vs. growth teams**: create shared KPIs (net good users acquired)
- **Static thresholds**: attackers adapt - refresh baselines, retrain, red-team new TTPs.

# 14. Investigator Checklist (Day-to-Day)

- Do multiple "users" share **phone/email/device/IP/address/payout**?
- Does the address resolve to the **same unit/PO box/freight forwarder**?
- Any **document anomalies** or **liveness failures**?
- Do accounts cluster in the **identity graph**? Who are the **bridges/mules**?
- Is there **promo timing** alignment (sign-ups right when incentives launch)?

# 15. Summary Takeways

- SIF is hard because it **manufactures trust** and avoids victim noise.
- Winning requires **entity resolution, duplication features, strong document/biometric checks, and graph-based detection**.
- Balance detection with **tiered KYC & progressive trust** to protect conversion while choking oof rings.

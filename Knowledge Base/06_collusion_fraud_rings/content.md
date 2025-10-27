# 📘 Module 6 - Collusion & Fraud Rings

## 0 TL;DR

Collusion & Fraud Rings involve **coordinated abuse by multiple entities (users, merchants, drivers, employees, partners)** who **cooperate to bypass independent fraud controls.**
They’re often discovered via **graph-based link analysis, temporal correlation, and unusual success rates across actors.**
Collusion can be _cross-role_ (buyer–seller, rider–driver, employee–merchant) or _cross-system_ (multiple platforms, shared infrastructure).
Detection requires **entity linkage, network analytics, and behavioral synchronization analysis**, not just individual anomaly detection.

## 1. Definition & Scope

- **Collusion**: Two or more entities collaborating (explicitly or tacitly) to exploit a platform, product, or incentive system.
- **Fraud ring**: A _structured network_ of colluding entities (accounts, devices, merchants, agents) designed to mimic legitimate activity while draining value.
- Can span across **customers, employees, vendors, and systems**.

Distinct from solo fraud:

- **Solo fraud** = single actor anomaly.
- **Collusion** = _distributed coordination_ where each participant may look normal in isolation but suspicious in aggregate.

## 2.Attacker Motivations

| Type                            | Typical Participants           | Motivation                                                           |
| ------------------------------- | ------------------------------ | -------------------------------------------------------------------- |
| **Buyer–Seller Collusion**      | Shoppers + Merchants           | Fake orders to inflate ratings or bonuses, trigger cashback/payouts. |
| **Rider–Customer Collusion**    | Delivery customer + rider      | Claim undelivered item; share refund or re-sell goods.               |
| **Employee–External Collusion** | Support agents + customers     | Approve false refunds, override risk checks for kickbacks.           |
| **Merchant–Courier Collusion**  | Restaurant + driver            | Fake completed orders to farm incentives.                            |
| **Multi-platform rings**        | Same ring across multiple apps | Exploit new-user promos everywhere; launder through wallets.         |

Structural forms:

- _Star topology_: single core account coordinating multiple peripherals.
- _Mesh topology_: everyone connected — typical of “bonus farms.”
- _Hierarchical_: ringleader recruits mules/actors with assigned roles.

## 3. Common Attack Vectors & TTPs

- **Fake transactions**: circular buying, self-orders, fake deliveries.
- **Referral pyramids**: one node seeds hundreds of “new users.”
- **Shared infrastructure**: same devices, IPs, payout accounts, or warehouse addresses.
- **Incentive farming**: colluding drivers/customers trigger streak/quest bonuses.
- **Refund collusion**: agents and customers approve ghost refunds.
- **Synthetic merchant webs**: shell stores to process fake volume and withdraw bonuses.
- **Data laundering**: moving small amounts through legitimate transactions to hide fraud flows.

## 4. Real-World Industry Examples

(a) E-commerce / Marketplace

- _Amazon India (2020–2022)_: rings of “verified” sellers colluded with fake buyers to inflate ratings and claim “fulfilled” sales for working-capital loans.
- _Shopee / Lazada promos_: merchant collusion with “buyers” to recycle vouchers and trigger refund schemes.

(b) Ride-hailing / Food Delivery

- _Grab / Uber Eats–style cases:_
  - Drivers and riders coordinate “cancel-rebook loops” to earn bonuses.
  - Ghost deliveries (driver never moves, GPS spoofing).

(c) Fintech / Wallets

- Rings that move small values across hundreds of accounts to evade transaction monitoring — a bridge between fraud and AML.

## 5. Business Impact

- **Direct loss**: fake payouts, bonus leakage, refund drains.
- **Indirect**: distorted metrics — fake GMV, fake DAU, inflated “active driver” counts.
- **Operational**: higher dispute rates, degraded ML model quality.
- **Compliance**: KYC and AML exposure if mules used for cash-out.
- **Reputation**: regulatory scrutiny, partner distrust, CX degradation.

## 6. Signals to Capture (Raw & Derived)

**Identity & Entity Linkage**

- Shared: phone numbers, emails, addresses, payout accounts, device fingerprints, IPs, bank accounts.

**Behavioral Synchrony**

- Unusually synchronized order times between “different” users.
- Circular transaction chains (buyer → seller → buyer → …).
- High mutual transaction overlap ratio.

**Operational / Incentive**

- High success rate of bonuses/refunds for certain subgroups.
- Drivers/riders with perfect acceptance/completion → but zero GPS movement.
- Agents whose refund approval rate > team mean + 3σ.

**Network Metadata**

- Referral edges forming dense, repeating patterns.
- Shared delivery addresses or pickup/drop-off points.
- Repeated use of same physical location by “different” merchants.

## 7. Feature Engineering for Collusion Detection

| Feature Type                | Example Feature                                                                               | Rationale                             |
| --------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------- |
| **Linkage Density**         | `shared_devices_count`, `shared_payment_accounts`, `shared_addresses`                         | Collusion entities share infra.       |
| **Graph Structure**         | `clustering_coefficient`, `betweenness_centrality`, `component_size`, `reciprocal_edge_ratio` | Network-level anomalies.              |
| **Behavioral Synchrony**    | `mean_time_gap_between_related_orders`, `geo_distance_vs_delivery_time`                       | Temporal/geo inconsistency.           |
| **Reward Abuse**            | `bonus_payout_ratio`, `referral_success_rate`                                                 | Over-performance = potential ring.    |
| **Text/Support**            | Similarity of claim language; same templates                                                  | Coordinated support manipulation.     |
| **Transaction Volume Flow** | Ratio of “in-ring” vs “out-ring” trades                                                       | Rings often recycle value internally. |

## 8. Graph & Network Analysis Approach

**Graph Construction**

- **Nodes**: all unique entities (users, merchants, devices, bank accounts, IPs, support agents).
- **Edges**: transactions, shared identifiers, referrals, payout links, co-locations.

**Detection Techniques**

1. **Community detection**: Louvain / Leiden clustering to find dense subnetworks.
2. **Centrality analysis**: Identify ring leaders (high degree or betweenness).
3. **Temporal coherence**: synchronized transactions; edge creation bursts.
4. **Link type weighting**: assign higher weight to hard identifiers (bank, device) vs soft (IP).
5. **Anomaly scoring**: graph embedding (node2vec / GraphSAGE) + isolation forest on embeddings.

**Visualization**

- Visualize rings with ForceAtlas2 or Graphistry.
- Color by role type (buyer, seller, driver).
- Time filter to see ring growth.

## 9. Labeling Challenges & Mitigations

**Why it’s hard**

- Evidence distributed: no single account “proves” fraud.
- Rings evolve fast: members churn in/out.
- Human review can’t confirm easily without context.

**Mitigations**

- Use weak labels via confirmed cases (e.g., refund collusion discovered → tag connected nodes).
- Expand using graph propagation or semi-supervised learning (lbel spreading).
- Time-slice validation (train on past quarter, detect new structures next quarter).
- Cross-domain correlation: if same nodes involved in multiple fraud types → raise confidence.

## 10. Modeling & Detection Strategies

**a. Rules + Heuristics**

- Shared device/IP + high transaction overlap → suspect ring.
- Repeated high bonuses between same pairs.

**b. Unsupervised / Graph-based**

- Graph clustering; anomaly detection in embeddings.
- Temporal subgraph comparison → detect fast-growing communities.

**c. Supervised (if labels exist)**

- Train on confirmed collusion clusters using features like centrality, reciprocity, edge weights.

**d. Hybrid Layering**

- Rule filters reduce candidate graph.
- ML scoring refines likelihood per edge or node.
- Human-in-the-loop investigations confirm cluster.

## 11. Organizational Detection Playbook

1. **Entity Resolution Layer**
   - Link users, merchants, devices, payments, addresses.
   - Deduplicate soft IDs (e.g., fuzzy address matching).
2. **Graph Modeling Layer**
   - Construct multi-entity graphs updated daily.
3. **Detection Layer**
   - Apply anomaly models, temporal growth detection.
4. **Review Layer**
   - Fraud Ops visualize clusters, verify patterns.
5. **Action Layer**
   - Freeze payouts, pause bonuses, block linked nodes.
6. **Feedback Layer**
   - Feed confirmed rings into feature store for retraining.

## 12. Business Process Controls (Preventive)

- **Bonus throttling**: set per-merchant/driver payout caps.
- **Referral dedup**: limit by device, payment instrument.
- **Payout cooling period**: hold funds until post-validation.
- **KYB/KYC checks**: verify merchant/driver ownership patterns.
- **Segregation of duties**: prevent single employee approving & disbursing.
- **Monitoring incentives**: “success rate anomalies” across cohorts.

## 13. Dashboards & Metrics

| Metric                                | Interpretation                        |
| ------------------------------------- | ------------------------------------- |
| Cluster size distribution             | Large dense clusters = possible rings |
| % of GMV within high-link clusters    | Volume at risk                        |
| Shared-entity counts (device/IP/bank) | Infrastructure overlap                |
| Bonus payout concentration (Gini)     | Payouts skewed to few actors          |
| Collusion recurrence rate             | Ring reactivation after takedown      |
| Detection-to-block time               | Operational efficiency                |

## 14. Common Pitfalls & How to Avoid

- **Siloed detection:** teams only monitor one role (buyers OR merchants). → Integrate cross-role data.
- **Over-blocking**: mistaking legitimate families/devices for collusion. → Use confidence scoring.
- **Static graphs**: failing to capture temporal drift. → Use rolling windows.
- **Ignoring internal actors**: employee collusion left unmonitored. → Add audit & access controls.
- **No cross-domain correlation**: rings evolve across fraud types. → Connect signals from ATO, promo, refunds, etc.

## 15. Investigator Checklist

- Shared infrastructure (device, IP, payout)?
- Mutual interactions or transaction cycles?
- High ratio of internal vs external trades?
- Timing patterns too synchronized to be random?
- Any insider (agent/employee) involved in approvals?
- Re-activation via new accounts after takedown?

## 16. Investigator Checklist

- Collusion rings = multi-actor, multi-domain fraud.
- Graph analysis and entity resolution are core capabilities.
- Successful detection requires combining behavioral synchrony, infrastructure linkage, and role correlation.
- Always think beyond the single user — fraud ecosystems behave like networks, not individuals.
- Balance automation with human investigation for context validation.

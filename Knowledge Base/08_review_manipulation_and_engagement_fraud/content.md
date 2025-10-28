# 📘 Module 8 - Review Manipulation & Engagement Fraud

## 0 TL;DR

Review and engagement fraud distort a platform’s reputation and ranking systems. Fraudsters use fake accounts, collusive groups, or automated bots to generate artificial positivity or negativity in ratings, reviews, likes, or follows. This undermines user trust, algorithmic fairness, and marketplace credibility.

## 1. Definition & Scope

| Term                      | Meaning                                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Review Manipulation**   | Any attempt to falsify user-generated ratings or text feedback to mislead customers or recommendation algorithms.                  |
| **Engagement Fraud**      | Artificial inflation or deflation of interaction metrics (likes, views, shares, follows) on social, marketplace, or app platforms. |
| **Astroturfing**          | Coordinated campaigns that simulate organic public opinion.                                                                        |
| **Reputation Laundering** | Using fake positive feedback to “wash” a poor real history.                                                                        |

## 2. Attacker Motivations & Economics

| Actor                  | Objective                     | Monetization                         |
| ---------------------- | ----------------------------- | ------------------------------------ |
| Sellers / Merchants    | Boost product rank & sales    | Higher conversion, search visibility |
| Competitors            | Sabotage rival listings       | Lower CTR & seller rating            |
| Agencies / Brokers     | Sell fake engagement packages | “5⭐ = $1 each” services             |
| Influencers / Creators | Inflate follower counts       | Sponsorships, brand deals            |
| Coordinated Groups     | Narrative manipulation        | Political or social influence        |

## 3. Common Attack Vectors

- **Fake Account Farms**: Thousands of accounts controlled via emulator racks.
- **Review Exchange Groups**: “You review mine, I review yours.”
- **Refund-for-Review**: Seller sends partial refund after positive rating.
- **Review Recycling**: Same text reused across products.
- **Botnets & Scripting**: Automated API calls generating views/likes/comments.
- **Defamation Raids**: Coordinated 1★ campaigns post-incident.

## 4. Business Impact

- **Erosion of Trust**: Customers no longer believe platform ratings.
- **Algorithmic Pollution**: Recommendation & ranking models trained on fake data.
- **Financial Loss**: Refunds, promotional misallocation, ad waste.
- **Regulatory Risk**: FTC, CMA, and EU DGA enforcement for deceptive reviews.
- **Operational Load**: Investigation backlogs, appeal handling costs.

## 5. Signals to Capture

| Signal Type            | Example Indicators                                             |
| ---------------------- | -------------------------------------------------------------- |
| **Textual / NLP**      | High n-gram overlap, unnatural sentiment, duplicate templates  |
| **Temporal**           | Review bursts within hours of product launch                   |
| **Behavioral**         | Same device reviewing multiple sellers; review/follow velocity |
| **Infra / Device**     | Shared IPs, device fingerprints, ASN clustering                |
| **Graph / Social**     | Reciprocal likes/reviews, dense reviewer–product communities   |
| **Purchase Integrity** | Unverified purchases, instant post-purchase review             |

## 6. Feature Engineering Examples

| Category | Feature                                             | Fraud Insight     |
| -------- | --------------------------------------------------- | ----------------- |
| Text     | `cosine_similarity_to_cluster`, sentiment variance  | Template spam     |
| Temporal | `reviews_per_hour`, burst duration                  | Campaign activity |
| Account  | `avg_time_since_signup`, `review_to_purchase_ratio` | Sockpuppets       |
| Infra    | `unique_IP_count_per_product`, ASN entropy          | Farm density      |
| Graph    | `mutual_review_ratio`, `edge_weight_by_similarity`  | Collusive rings   |

## 7. Graph & Network Analytics

**Graph Schema**

- **Nodes**: users, products, sellers, devices, IPs
- **Edges**: wrote_review, shared_IP, shared_device, liked

**Detection Tactics**

- Community detection (Louvain, Leiden) for dense clusters.
- Edge weighting by review similarity or temporal proximity.
- Centrality analysis to find brokers coordinating rings.
- Temporal evolution graphs to spot campaign bursts.

## 8. Labeling & Ground Truth Challenges

| Challenge     | Description                          | Mitigation                                         |
| ------------- | ------------------------------------ | -------------------------------------------------- |
| Ambiguity     | Enthusiastic users vs paid reviewers | Confidence tiers & manual spot checks              |
| Sparse labels | Only small portion confirmed         | Weak supervision from takedowns & broker lists     |
| Bias          | Over-sampling obvious cases          | Cluster-level labeling to capture subtler patterns |
| Evolution     | New spam templates monthly           | Rolling retraining & drift monitoring              |

## 9. Detection Approaches

**Rules / Heuristics**

- Rate-limit reviews per IP/day.
- Require verified purchase before review visibility.
- Flag high-burst posting or extreme rating swings.

**Supervised ML**

- Gradient-boosted trees on behavioral & NLP features.
- Multi-input models (text + metadata).

**Unsupervised / Graph ML**

- Embedding clustering, graph autoencoders, link-prediction anomalies.

**Hybrid Workflow**
1️⃣ Rules flag clusters →
2️⃣ ML ranks by risk →
3️⃣ Graph expands network →
4️⃣ Ops Team validates → labels feedback to model.

## 10. Governance & Platform Controls

- **Transparency**: Mark “Verified Purchase” & display review age.
- **Incentive Design**: Prohibit refunds/rewards tied to reviews.
- **Automation Limits**: CAPTCHA, behavior throttling, device registration.
- **Appeals System**: Fair removal & reinstatement pipeline.
- **Cross-Platform Sharing**: Broker IP lists, domain blacklists.

## 11. Metrics & Dashboards

| KPI                          | Purpose               |
| ---------------------------- | --------------------- |
| Review Burst Count / Day     | Campaign monitoring   |
| Verified vs Unverified Ratio | Policy compliance     |
| Text Similarity Entropy      | Diversity check       |
| Account per Device /IP       | Farm detection        |
| Appeal Reversal Rate         | Precision measurement |
| Rating Volatility Index      | Manipulation impact   |

## 12. Common Pitfalls & Mitigations

| Pitfall                     | Consequence                         | Fix                          |
| --------------------------- | ----------------------------------- | ---------------------------- |
| Over-aggressive takedowns   | Harm legitimate reviewers           | Confidence scoring & appeals |
| Ignoring event context      | False positives during sales events | Baseline normalization       |
| Siloed NLP vs Infra signals | Missed collusion                    | Unified graph pipeline       |
| Static thresholds           | Attackers adapt                     | Adaptive baselines           |
| No feedback loop            | Model drift                         | Continuous label refresh     |

## 13. Investigator Checklist

- Same IP/device posting many reviews?
- Text template reuse > 80 % similarity?
- Rating swing pattern after launch/promo?
- Reciprocal review network detected?
- Unusual merchant growth post burst?
- Broker domain or external referral trace?

## 14. Key Takeaways

- Review & engagement fraud = reputation manipulation economy.
- Cross-signal fusion (text + behavior + infra + graph) is mandatory.
- Detection success = balance between accuracy and user fairness.
- Continuous feedback & education reinforce trust.
- Collaboration between Fraud Analytics × T&S × Policy is essential.

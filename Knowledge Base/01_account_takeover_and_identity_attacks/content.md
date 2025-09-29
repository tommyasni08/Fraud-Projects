# 📘 Module 1 - Account Takeover (ATO) & Identity Attacks

## 1. Definition

Account Takeover (ATO) is when a bad actor gains **unauthorized access** to an existing user's account in order to commit fraud, theft, or abuse.

- **Key difference vs New Account Fraud (NAF)**:
  - ATO = attacker hijacks a _legimate_ users's account (harder to detect, higher trust).
  - NAF = attacker creates a _new fake account_ (caught more easily by onboarding/KYC controls).

## 2. Motivations (Why Attackers Pursue ATO)

- **Fintech/Banks**: drain balances, send fraudulent transferss, launder money.
- **E-Commerce/Marketplaces**: steal loyalty points, abuse saved cards, resell vouchers, commit refund fraud.
- **Ride-Hailing/Delivery**: steal promo credits, create phantom rides/deliveries, harvest driver incentives.
- **Social Platforms**: spread scams/spam via trusted accounts, impersonate verified users, manipulate discourse.

👉 In short: ATO = a shortcut to trust + money + reputation.

## 3. Attack Vectors

- **Credential Stuffing**: Using leaked password/email combos from breaches.
- **Phising**: Trick users into giving credentials via fake sites/messages.
- **Social Engineering**: Convince victims to hand over OTPs or reset codes.
- **SIM Swap**: Hijack phone numbers to intercept 2FA SMS.
- **Malware/Keyloggers**: Steal crendetials directly from infected devices.
- **Brute Force**: Repeated password guessing (rarely effective if defenses exist).

## 4. Case studies

- **OCBC Bank (Singapore, 2021)**: Over 790 customers lost SGD $13M due to phising SMS that redirected to fake websites; attackers captured logins + OTPs.
- **Robinhood (US, 2021)**: Credentials stuffing from external breaches led to customer accounts drained and data exfiltrated.
- **Twitter (2020)**: High-profile verified accounts (Elon Musk, Obama, etc.) were compromised and used to push a Bitcoin scam.

## 5. Business Impact

- **Financial**: Direct reimbusement losses, chargebacks, fines.
- **Trust/Reputation**: Customers abandon platforms they see as unsafe.
- **Compliance**: Regulators may impose penalties (e.g. GDPR, MAS in Singapore, US OCC).
- **Operational**: Fraudulent accounts pollute data -> corrupt business metrics, harm model accuracy.

## 6. Signals for Detection

- **Login Metadata**: IP, ASN, device fingerprint, OS/browser, time-of-day.
- **Geo-velocity/Impossible Travel**: Two logins far apart in short time.
- **Device Posture**: New/unseen devices, emulator or rooted phones.
- **Behavioral Biometrics**: Typing cadence, navigation speed.
- **Session Actions**: Password resets, payout edits, bulk messages/transactions soon after login.
- **Cross-Entity Signals**: Same device/IP across multiple accounts.

## 7. Anomaly Detection Techniques

- **Rule-based**: ">5 failed logins in 5 minutes," ">500km traveled in <1hr."
- **Statistical**: Z-scores for login frequency, deviation from user's baseline.
- **Unsupervised ML**: Isolation forests, clustering on login features.
- **Supervised ML**: Gradient boosting or neural nets trained on labeled fraud/non-fraud sessions.
- **Risk Scoring**: Outputting a score (low,medium,high) -> tied to progressive friction.

## 8. Data & Labeling Challenges

- **Delayed Labels**: Fraud confirmed only after weeks (complaints, chargebacks).
- **Ambiguity**: Social engineering cases - user "gave" access voluntarily.
- **False Positives**: Travelers using VPNs can look like ATO.
- **Data Quality**: Session logs may be incomplete (e.g., mobile network IP churn).

**Mitigation**: feedback loops, manual review teams, probalistics labels, synthetic training, data (e.g. simulation credential-stuffing).

## 9. Modeling Angle (Predictive Features)

When designing an ATO model, typically predictive features include:

- **Login Metadata**: IP risk score, ASN type, distance from last login, time-of-day-anomaly.
- **Behavioral**: Time-to-transaction after login, unusual action sequences, transaction velocity.
- **Acount Lifecycle**: Recent password reset, email/phone change, 2FA disable attempts.
- **Cross-Entity**: Device/IP overlap with other accounts, shared payout endpoints.
- **Entropy/Diversity**: Distribution of device/browser strings (too uniform = bot farm, too random=obfuscation attempt).

## 10. Balancing Security & User Experience

- **Progressive Friction**:
  - Low risk -> allow.
  - Medium risk -> OTP challenge or re-auth.
  - High risk -> block session or force reset.
- **Trade-off**: Too strict = frustrated good users (false positives); too lenient = high fraud leakage.
- **Metric**: Safety-friction balance measured by fraud catch rate vs false positive appeal overturn rate.

# ✅ Key Takeaways

- ATO is **universal across industries** - it exploits existing trust, making it more damaging than new account fraud.
- Analysts must think in **multi-layered signals** (login metadata, behavior, network, device).
- Data scientist/engineers must handle **weak labels**, design **robust features**, and evaluate models but not just by accuracy but by **business trade-offs**.
- Success = minimizing fraud and false positives while protecting user experience.

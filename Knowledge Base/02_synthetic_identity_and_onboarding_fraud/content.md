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

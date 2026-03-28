# Fraud Prevention & Account Security Policy

**Document ID:** POL-FP-010  
**Effective Date:** January 1, 2026  
**Last Updated:** March 18, 2026  
**Department:** Trust & Safety  
**Classification:** Internal Policy — Confidential (Customer-Facing Summary)  

---

## 1. Overview

This policy outlines The Platform's approach to fraud prevention, account security, unauthorized access, and identity theft protection. It applies to all customer accounts and transactions on the platform.

## 2. Account Security

### 2.1 Password Requirements
- Minimum **8 characters** with at least one uppercase letter, one lowercase letter, one number, and one special character
- Passwords are hashed using **bcrypt** and never stored in plaintext
- Password reuse of the last 5 passwords is not permitted
- Account lockout after **5 consecutive failed login attempts** (30-minute lockout, extendable)

### 2.2 Two-Factor Authentication (2FA)
- Available for all accounts; **mandatory** for Platinum tier members
- Supported methods: SMS code, authenticator app (Google Authenticator, Authy), email code
- 2FA is required for: password changes, payment method changes, address additions, and orders over $500

### 2.3 Account Recovery
- Customers who lose access can recover their account through:
  1. **Email verification:** A reset link sent to the registered email
  2. **Phone verification:** An OTP sent to the registered phone number
  3. **Identity verification:** Upload of a government-issued ID (processed within 24-48 hours)
- Account recovery resets the 2FA settings, and the customer must re-enable 2FA after accessing their account

## 3. Transaction Fraud Detection

### 3.1 Automated Screening
Every transaction is screened in real-time for fraud indicators:
- **Address Verification System (AVS):** Billing address is checked against the card issuer's records
- **Card Verification Value (CVV):** Required for all card transactions
- **Velocity checks:** Multiple orders from the same account, IP, or card within a short period
- **Behavioral analysis:** Unusual browsing patterns, rapid price-point escalation, or large first-time orders
- **Device fingerprinting:** Identification of device attributes to detect known fraudulent devices

### 3.2 Manual Review Triggers
Orders are escalated for manual review if they exhibit:
- Shipping address in a different country from the billing address (for first-time orders)
- Order value exceeding **$1,000** (first-time customers only)
- Multiple payment method failures followed by a successful payment
- Use of known fraud-associated email domains or proxy/VPN IP addresses
- Request for overnight shipping on high-value electronics (first-time customer)

### 3.3 Review Process
- Manual reviews are completed within **2-4 hours** during business hours, **8-12 hours** outside business hours
- During review, the order is placed on "Payment Verification" hold — the customer sees a notification explaining the delay
- If the order passes review, it proceeds to fulfillment
- If the order fails review, it is cancelled, the payment is voided, and the customer is notified with next steps (identity verification or alternative payment)

## 4. Unauthorized Account Activity

### 4.1 Detection
The Platform monitors for unauthorized account activity including:
- Logins from new devices or locations
- Changes to payment information
- Changes to shipping addresses
- Unusual order patterns

### 4.2 Customer Reporting
If a customer suspects unauthorized activity:
1. **Immediately** contact The Platform support via the "Report Unauthorized Activity" button in Account Settings or by calling the Priority Security Line
2. The Platform freezes the account within **15 minutes** of a verified report
3. All pending orders are held for review
4. Recent orders (last 72 hours) are reviewed for unauthorized transactions

### 4.3 Resolution
- Unauthorized transactions are fully reversed (refunded) within **3 business days** of confirmation
- The customer receives a new account with transferred loyalty status and points (if verified identity match)
- A detailed incident report is provided to the customer for their records (useful for filing police reports)
- The Platform cooperates with law enforcement investigations when required

## 5. Refund Fraud Prevention

### 5.1 Empty Box / Wrong Item Return Fraud
- All returned items are inspected at the fulfillment center before refunds are processed
- Weight verification is performed on received packages and compared to expected weight
- Serial numbers (for electronics) are checked against the original shipment
- Discrepancies result in refund denial and investigation

### 5.2 Claim Abuse Patterns
Accounts flagged for potential claim abuse:
- **3 or more** "item not received" claims within 6 months
- Return rate exceeding **40%** of purchases in any 90-day period
- Multiple claims on high-value items ($200+) within a short period
- Claims that contradict delivery photo evidence

### 5.3 Consequences
- First offense: Warning email and account flag
- Second offense: Loss of return privileges for 90 days
- Third offense: Account suspension pending review by Trust & Safety
- Confirmed fraud: Permanent account ban, referral to law enforcement, and debt collection for any unrecovered funds

## 6. Identity Theft Protection

### 6.1 If a Customer's Identity Is Used to Create a The Platform Account
- The victim should contact The Platform immediately with:
  1. A government-issued photo ID
  2. A police report or FTC Identity Theft Report
  3. Any The Platform order numbers or account details if known
- The Platform will close the fraudulent account within **24 hours** of verification
- Any outstanding charges or collections associated with the fraudulent account are halted
- The Platform issues a letter confirming the identity theft for the victim's records

### 6.2 Data Breach Notification
- In the event of a data breach affecting customer data, The Platform will:
  1. Notify affected customers within **72 hours** of discovery (per regulatory requirements)
  2. Provide free credit monitoring for **12 months**
  3. Reset all affected account passwords
  4. Offer identity theft insurance through a partner service

---

**Policy Contact:** security@The Platform.com  
**Urgent Security Line:** 1-800-SHOP-SEC (available 24/7)  
**Escalation:** Account security → Trust & Safety Lead at trust-safety@The Platform.com  
**Policy Owner:** Chief Security Officer  

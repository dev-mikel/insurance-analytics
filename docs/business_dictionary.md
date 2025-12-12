# **Business Dictionary Document (Insurance Analytics Demo)**

### *Version 1.0 — Business & Non-Technical Audience Edition*

---

# **0. Table of Contents**

1. [Insurance Customer & Demographic Concepts](#1-insurance-customer--demographic-concepts)
2. [Policy Concepts & Coverage Terminology](#2-policy-concepts--coverage-terminology)
3. [Claims Concepts & Loss Terminology](#3-claims-concepts--loss-terminology)
4. [Underwriting & Quote Funnel Concepts](#4-underwriting--quote-funnel-concepts)
5. [Pricing, Premium & Actuarial Concepts](#5-pricing-premium--actuarial-concepts)
6. [Retention, Churn & Customer Engagement Concepts](#6-retention-churn--customer-engagement-concepts)
7. [Geography & Segmentation Concepts](#7-geography--segmentation-concepts)
8. [KPIs Used Across the Project](#8-kpis-used-across-the-project)
9. [Business-Relevant Derived Metrics](#9-businessrelevant-derived-metrics)
10. [Fraud, Risk & Severity Concepts](#10-fraud-risk--severity-concepts)

---

# **1. Insurance Customer & Demographic Concepts**

### **Customer**

A person who holds or requests one or more insurance policies.

### **Customer ID**

A unique identifier assigned to each customer.

### **Age**

Customer’s age at acquisition or underwriting.

### **Income**

Annual household or personal income. Used for segmentation (e.g., high-income groups).

### **BMI (Body Mass Index)**

A measure of body weight relative to height.
Example:
BMI = 22.5 (normal), BMI = 33 (higher health risk).

### **Gender / Occupation / Marital Status**

Demographic attributes often used for statistical segmentation.

### **Acquisition Channel**

How the customer was acquired:

* *Agent*
* *Broker*
* *Digital* (online self-service)
* *Referral*

### **Acquisition Date**

Approximate date when the customer first engaged with the insurer.

---

# **2. Policy Concepts & Coverage Terminology**

### **Policy**

A formal insurance contract covering specific risks for a customer.

### **Policy ID**

Unique identifier for each policy.

### **Product Line**

The category of insurance product, e.g.:

* Auto
* Health
* Property
* Life

### **Coverage Amount**

The maximum amount the insurer will pay for a covered loss.
Example: Auto policy with USD 30,000 coverage.

### **Deductible**

Portion of the loss the customer must pay before insurance coverage applies.
Example:
Loss = 5,000, Deductible = 1,000 → Insurer pays 4,000.

### **Premium (Annual Premium)**

Amount the customer pays yearly for the policy.
Determined based on risk, product features, and pricing strategy.

### **Payment Frequency**

How the customer pays premiums:

* Monthly
* Quarterly
* Annually

### **Start Date / End Date**

The policy’s coverage period.

### **Tenure**

Policy age or the number of years the customer has held the policy.

### **Risk Score (0–100)**

A numeric indicator of expected risk of future claims.
Higher values = higher expected risk.

### **Risk Class**

A qualitative classification of risk:

* LOW
* MEDIUM
* HIGH (or Preferred / Standard / Substandard / Declined under advanced UW rules)

---

# **3. Claims Concepts & Loss Terminology**

### **Claim**

A request by the customer for payment due to a loss.

### **Claim ID**

Unique identifier for each claim.

### **Occurrence Date**

When the loss happened (accident, damage, incident).

### **Report Date**

When the customer informs the insurer.

### **Settlement Date**

When the claim is fully resolved and paid.

### **Claim Amount (Incurred Loss)**

Total amount of loss the customer experiences.

### **Net Paid**

What the insurer actually pays after subtracting the deductible:
Net Paid = max(Claim Amount − Deductible, 0)

### **Severity**

The size of the loss (how expensive each claim is).
Typically modeled using statistical distributions (lognormal, gamma).

### **Frequency**

Number of claims that occur within a period or among a group of policies.

### **Fraud Score**

Indicator (0–100) of potential fraud risk in a claim, based on:

* Delay in reporting
* Severity vs expected
* Legal representative involvement
* Customer history

### **Legal Representation Flag**

Whether the claimant is represented by an attorney.

---

# **4. Underwriting & Quote Funnel Concepts**

### **Underwriting (UW)**

Process where the insurer assesses risk and decides whether to issue a policy.

### **Quote**

A price offer made to a customer.

### **Quote Status**

Shows the stage of an insurance purchase:

* REQUESTED
* QUOTED
* ACCEPTED
* BOUND (policy issued)
* DECLINED
* EXPIRED

### **STP (Straight-Through Processing)**

Automation level where a quote is approved without manual underwriting.

### **Accepted Flag**

Customer accepted the quote.

### **Bound Flag**

Policy is officially activated and issued.

### **Expired Flag**

The customer did not act on the quote within the expected time.

---

# **5. Pricing, Premium & Actuarial Concepts**

### **Technically Required Premium (TRP)**

The minimum premium needed to cover:

* Expected losses
* Risk load
* Operational/expense load
* Capital requirements

### **Pure Premium**

Expected loss cost:
Exposure × Expected Frequency × Expected Severity.

### **Base Rate / Base Factor**

Multipliers used in pricing to obtain TRP.

### **Market Average Premium**

Premium observed in the marketplace for similar insureds.

### **Pricing Segment**

Group of policies by shared attributes (e.g., product_line + state).
Used to compare pricing adequacy and competitive position.

### **Loss Development**

Tracking how claims costs evolve over time (12m, 24m, 36m development).

---

# **6. Retention, Churn & Customer Engagement Concepts**

### **Retention**

Percentage of customers renewing their policies.

### **Churn**

Customer stops doing business with the insurer.

### **Churn Flag**

Boolean indicator marking churned customers.

### **Churn Date**

Date when the customer left the insurer.

### **Churn Reason**

Classified cause of churn:

* Price
* Service issues
* Competitor offer
* Life change
* Payment problems

### **Campaign Executed**

Whether a retention or marketing campaign targeted the customer.

### **Responded Flag**

Whether the customer engaged with the campaign.

### **Retained After Campaign**

True if the customer stayed after a retention effort.

### **Engagement Score**

Numeric measure (0–100) of customer activity or loyalty.

### **NPS (Net Promoter Score)**

Customer satisfaction metric from 0 to 10.

---

# **7. Geography & Segmentation Concepts**

### **Region**

High-level geographical segmentation (e.g., north_east, mid_west).

### **State**

Subregion within a region (NY, TX, CA, etc.).

### **Exposure**

Number of active policies in a particular segment.

---

# **8. KPIs Used Across the Project**

### **Loss Ratio (LR)**

LR = Incurred Loss / Earned Premium
Measures profitability:

* LR < 1.0 is desirable
* LR > 1.0 means losses exceed premium revenue

### **Frequency KPI**

Percentage of policies with at least one claim.

### **Severity KPI**

Average claim size.

### **Combined Ratio (not implemented but related)**

LR + Expense Ratio.

### **Quote Rate**

Percentage of quote requests that progress to “QUOTED”.

### **Acceptance Rate**

Percentage of quotes accepted by customers.

### **Bind Rate**

Percentage of accepted quotes that result in an issued policy.

### **Churn Rate**

Percentage of customers who leave during a period.

### **Retention Rate**

Opposite of churn; percentage retained.

---

# **9. Business-Relevant Derived Metrics**

### **Risk Adjustment Score**

Combines demographic factors and product characteristics into a score used for pricing or underwriting.

### **Premium Adequacy**

Comparison between actual premium and technically required premium.

### **Exposure Count**

Number of policies contributing to a pricing segment.

### **Fraud Indicator**

High fraud_score + long reporting delay + legal representation → suspicious case.

### **Policy Conversion Funnel**

REQUESTED → QUOTED → ACCEPTED → BOUND
Shows customer acquisition efficiency.

---

# **10. Fraud, Risk & Severity Concepts**

### **Fraud Triangle Factors (simplified)**

Indicators that increase risk of fraudulent claims:

* Delay between occurrence and report
* Severity unusually high relative to coverage
* Attorney involvement
* Customer’s prior history

### **Risk Class Mapping**

Categorization of customer risk for underwriting or pricing.

### **Severity Distribution**

Mathematical model used to simulate claim costs.
Examples:

* Lognormal for Auto or Property (high-variability events)
* Gamma for Health (moderate variability)
* Fixed for Life benefits

---

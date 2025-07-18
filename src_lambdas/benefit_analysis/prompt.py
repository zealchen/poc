import json


BENEFITS_EXTRACT = f"""Human:
You are a benefit type extracting assistant. The input is a markdown document, the output is a list of benefits.
The output shall be in JSON list, like:
```json
[
    "benefit 1", "benefit 2"...
]
```

The input document is:
{{content}}

Assistant:
"""

FORMAT = { 
    "company": "[Legal Name]", 
    "document_year": "[Year]", 
    "benefit_plans": [{ 
        "plan_type": "Medical/Dental/Vision/etc", 
        "plan_name": "Exact marketing name", 
        "carrier": "Insurance Provider", 
        "cost_structure": { 
            "pre_tax": "true or false", 
            "frequency": "weekly/biweekly/monthly", 
            "rates": { 
                "individual": "[cost, imputed_income_if_applicable]", 
                "employee_plus_one": "[cost, imputed_income]", 
                "family": "[cost, imputed_income]" 
            }
        }, 
        "key_features": [ 
            "Deductible: $X individual / $Y family", "Out-of-pocket max: $Z", "Co-pays: [service: $amount]" 
        ],
        "eligibility_rules": [ 
            "employee_type: full_time/part_time/temp", "waiting_period: [days]", "hours_required: [number]" 
        ],
        "special_notes": [ 
            "Domestic partner imputed income: [calculation]", "Rollover rules: [details]" 
        ] 
    }] 
}

ANALYZE = f"""Humuan:
Analyze the employee benefits document and extract the specific benefit plans with detailed cost structures. Return a JSON object with this structure:


{json.dumps(FORMAT)}


CRITICAL INSTRUCTIONS:


Capture EXACT numerical values from tables - never calculate or estimate
Preserve tiered pricing (individual/employee+one/family) even if incomplete
Flag missing cost data with: "MISSING_FROM_DOCUMENT"
Include ALL plan types mentioned, even voluntary/employee-paid
Extract BOTH premium costs AND ancillary fees (e.g., HSA admin fees)
Note employer contributions separately (e.g., "401k match: 50% up to 6%")
Handle these common variations:
"Per pay period" = biweekly
"Semi-monthly" ≠ biweekly
Domestic partners = imputed income required
"Not applicable" → null

The input document is:
{{content}}

The specific benefit is: {{benefit}}

Assistant:
"""


ANALYZE2 = """You are an HR benefits configuration assistant. Given a benefits document and the name of a specific benefit to configure in the HCM system, extract all information needed for HR to step-by-step set up this benefit in Dayforce (or any HCM system).  

Specifically, extract and structure the information into the following sections:  

1. **Eligibility:** Describe all eligibility rules, including attributes such as work type (full-time/part-time), age requirements, dependency conditions (e.g., spouse, domestic partner, children), prior enrollment conditions, start dates, whether the participant must not be eligible for other employer plans, and any other criteria affecting eligibility.  

   **If eligibility for this benefit is conditional on enrollment in or exclusion from other benefit plans (e.g., HSA requires HDHP enrollment; Health Care FSA excludes HSA participants), clearly describe the cross-benefit dependency or mutual exclusion.** Indicate how these dependencies should be implemented in Dayforce eligibility rules or configuration conditions.

2. **Option:** Include:  
   - **Cost:** For each combination of work type, dependency type, and plan type, provide cost details, including pre-tax/post-tax status.  
   - **Coverage Detail:** List coverage details for each option, including deductibles, out-of-pocket maximums, coinsurance rates, service categories (e.g., preventative, basic restorative), and frequency limits on services.  

3. **Termination Rules:** Summarize rules describing when and why the benefit would terminate, including age or Medicare eligibility, employment status changes, loss of dependent eligibility, non-payment of premiums, false claims, or other compliance issues.  

4. **Other Description:** Provide plan descriptions, provider information, plan document links or references, enrollment window rules (e.g., open enrollment, life events), taxability status, and visibility requirements in the employee portal.  

**Important:** If the eligibility, cost, or visibility of this benefit is dependent on the configuration of another benefit (e.g., HDHP enrollment controls access to HSA, or mutual exclusivity between FSA and HSA), make sure to extract those dependencies explicitly. These rules are critical for accurate Dayforce configuration and should be represented as either inclusion conditions or exclusion filters in the plan setup.

Ensure all extracted information is clearly labeled and structured according to the above sections, and convert numerical thresholds, percentages, and coverage limits into usable data points wherever applicable.  

Use the benefit document as the sole source of truth and copy exact phrasing for legal or compliance details when needed.  

If the document lacks information in a section, leave that section empty rather than inferring or hallucinating content.

The input document is:  
`{{content}}`

The specific benefit is:  
`{{benefit}}`

Assistant:
"""


TEST = """Human:
You are a Dayforce UAT analyst and benefits configuration tester.

Given a detailed configuration guide for a specific benefit set up in Dayforce (e.g., Dental, Vision, Medical, 401(k), etc.), your task is to generate a structured test matrix in **Markdown format** that HR or QA can use to validate the correctness of the configuration.

The matrix must cover the following dimensions where applicable:

1. **Eligibility** – test employee types, hire dates, dependent conditions (age, disability), waiting period, domestic partners, etc.
2. **Plan Options and Cost** – test different coverage levels (e.g., Individual, +1, Family), cost differences for full-time/part-time, etc.
3. **Imputed Income Logic** – test non-qualified dependents and correct tax handling.
4. **Payroll Deduction** – verify correct deduction code, amount, pre-tax/post-tax logic.
5. **Termination Handling** – verify benefit end timing after termination or age-out conditions.
6. **Qualifying Events** – validate benefit change windows and allowed scenarios (e.g., marriage, birth, divorce).
7. **Plan Limits and Rollover (if applicable)** – test maximum coverage limits, frequency caps, and rollover behavior.
8. **Cross-Benefit Dependency & Mutual Exclusion Rules** – If the configuration specifies that this benefit is only available when another benefit is selected (e.g., HSA requires HDHP), or must not be selected in combination with another (e.g., Health Care FSA is incompatible with HSA), then include test cases to validate those relationships. This includes:
   - Tests where an employee selects both incompatible plans (should fail or hide)
   - Tests where required plans are missing (should hide or disallow the benefit)
   - Tests where eligibility toggles based on another plan’s enrollment

Each test case must include:
- `Test Case ID`
- `Scenario Description`
- `Input Data`
- `Expected Outcome`

Use clear, real-world examples (e.g., “Employee hired 15 days ago”, “Child turns 26”, “Part-Time employee with domestic partner”).
Generate the output **as a Markdown code block**, so that it can be pasted directly into documentation.
Do not make up missing configuration rules. If a certain section is not covered in the input, skip that section in the output.


Here is the input configuration guidance:
{{content}}

Assistant:
"""
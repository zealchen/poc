# Delta Dental PPO Plus Premier Test Matrix

## 1. Eligibility

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| ELIG-01 | Full-Time employee hired 20 days ago | Employee type: Full-Time (35+ hrs), Hire date: 20 days ago | Not eligible for coverage (30-day waiting period not met) |
| ELIG-02 | Part-Time employee (30 hrs) hired 45 days ago | Employee type: Part-Time (24–34 hrs), Hire date: 45 days ago | Eligible for coverage (30-day waiting period met) |
| ELIG-03 | Employee adds domestic partner without affidavit | Dependent: Domestic partner (no notarized affidavit/24-month evidence) | Dependent rejected until documentation provided |
| ELIG-04 | 25-year-old dependent child | Dependent: Biological child (age 25) | Eligible for coverage |
| ELIG-05 | 27-year-old disabled dependent | Dependent: Child (age 27) with disability documentation | Eligible for coverage |

## 2. Plan Options and Cost

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| COST-01 | Full-Time employee selects "Family" coverage | Employee type: Full-Time, Coverage: Family | Weekly deduction: $10.22 (pre-tax) |
| COST-02 | Part-Time employee selects "Employee +1" | Employee type: Part-Time, Coverage: Employee +1 | Weekly deduction: $8.79 (pre-tax) |
| COST-03 | Full-Time employee with 3 non-qualified dependents | Coverage: Family, 3 non-qualified dependents | Imputed income: $34.05/week (post-tax) added |

## 3. Imputed Income Logic

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| IMPUT-01 | Employee +1 non-qualified dependent | Coverage: Employee +1 (non-qualified domestic partner) | $10.99/week imputed income (post-tax) |
| IMPUT-02 | Employee +2 non-qualified dependents | Coverage: Family (2 non-qualified dependents) | $34.05/week imputed income (post-tax) |

## 4. Payroll Deduction

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| PAY-01 | Full-Time employee with qualified dependents | Coverage: Family (all qualified dependents) | $10.22/week pre-tax deduction (no imputed income) |
| PAY-02 | Part-Time employee with 1 non-qualified dependent | Coverage: Employee +1 (non-qualified) | $8.79 pre-tax + $10.99 post-tax deduction |

## 5. Termination Handling

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| TERM-01 | Voluntary termination | Termination date: 2024-03-01 | Coverage ends 2024-03-06 (5 calendar days later) |
| TERM-02 | Dependent turns 26 (non-disabled) | Dependent birthdate: 1998-02-15 (current date: 2024-02-16) | Coverage ends 2024-02-16 |

## 6. Qualifying Events

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| QE-01 | Marriage mid-year | Qualifying event: Marriage (2024-06-01) | Allow spouse addition within 30 days |
| QE-02 | Birth of child outside Open Enrollment | Qualifying event: Child birth (2024-04-15) | Allow family coverage upgrade within 30 days |

## 7. Plan Limits and Rollover

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| LIMIT-01 | Claim exceeds annual maximum | Total claims: $2,100 in 2024 | $2,000 covered, $100 patient responsibility |
| LIMIT-02 | Rollover eligibility (met conditions) | Enrolled before Q4 2023, had 2023 cleaning, $1,800 unused | $200 rolled over to 2024 (preset limit) |
| LIMIT-03 | Crown replacement before 60 months | Crown placed 2022-01-01, replacement requested 2024-03-01 | Claim denied (60-month frequency rule) |

## 8. Service Category Validation

| Test Case ID | Scenario Description | Input Data | Expected Outcome |
|--------------|-----------------------|------------|------------------|
| SVC-01 | Third fluoride treatment for 17-year-old | Patient age: 17, 3rd fluoride request in 2024 | 2 treatments covered, 3rd denied |
| SVC-02 | Implant replacement after 5 years | Implant date: 2019-03-01, replacement 2024-03-15 | 50% coverage after deductible |
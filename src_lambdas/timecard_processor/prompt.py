TIMECARD = f"""Please extract all records and total amount from the attached timecard image. For each record, provide the following fields firstly:
- ACCT NO
- JOB NO
- QUANTITY
- RATE
- HOURS
- AMOUNT
- DESCRIPTION OF WORK
- EMPLOYEE NAME
- HIRE DATE
- SHIFT
- MO_DAY_YR
- COST CENTER
- CLOCK

If a field is not present, leave it blank.
Then double check the correctness of the hours and amount field with the total hours and amount data you extract from the image.
Make sure the data in each column could sum up to the total hours and amount.

Finally, format the output as a JSON object with two keys: "records" and "totals".
The "records" key should contain a JSON array of objects, where each object represents a single record.
The "totals" key should contain a JSON object with the following keys: "Total Hours", "Total Amount", "Corrections".
*BE SURE* all the values you output is extracted from the image, not by your assumption.
For example:
```json
{{
    "records": [
        {{
            "ACCT NO": "123",
            "JOB NO": "456",
            ...
        }},
        {{
            "ACCT NO": "789",
            "JOB NO": "101",
            ...
        }}
    ],
    "totals": {{
        "Total Hours": "",
        "Total Amount": "",
        "Corrections": ""
    }}
}}
```
"""
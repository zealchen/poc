TEST_GENERATION = """
Generate a QTI v3.0 test item for the Massachusetts Comprehensive Assessment System (MCAS) based on the following specifications.
Subject: {subject}
Grade Level: {grade_level}
Curriculum Category: {category}
Curriculum Requirement: {requirement}
QTI Type: {qti_type}
QTI XML Example:
```xml
{example_xlm}
```

Universal Standards:
- Bias and Sensitivity: Ensure content is free of bias, stereotypes, and insensitive language. Scenario should be culturally appropriate and relatable to diverse students.
- Factual Accuracy: All factual information must be unequivocally correct. For math problems, ensure calculations and concepts are accurate.
- Content Design: Question and components must be clearly, precisely, and unambiguously worded, considering potential confusion for English learners.

Content Alignment:
- Passage Based: Question must include a high-quality reading passage
- Grade-appropriate: Passage must be appropriate in word count, concepts, vocabulary, and readability for 4th grade
- Copyright-free: Use only public domain content

Item Components:
- Question Stem: Clear question/prompt including required passage
- Correct Answer: Correct response with rationale
- Gap Elements: Multiple plausible options for gap-match interaction

XML Formatting Requirements (CRITICAL):
- Use ONLY full opening and closing tags: <tag></tag>
- NEVER use self-closing tags like <tag/>
- Even for empty elements, use the full format: <qti-gap identifier="G1"></qti-gap>
- This applies to ALL XML elements without exception

Output Format:

```json
{
    "rationale_for_correct_answer": "str",
    "rationale_for_distractors": "str", 
    "universal_design_considerations": "str",
    "qti_xml": "str"
}
```
"""

TEST_VERIFICATION = """
Check the following test item:
{test_content}

For each requirement:
### Content/Passage/Curriculum Alignment

- **Passage Based** - A question must be associated with a high-quality reading passage.
- **Passage must be grade-appropriate** in word count, concepts, vocabulary, and readability.
- **Written permission must be secured from copyright holders** to reprint passages.

### Clarity/Quality/Structural Verification

- **Clear/Unambiguous wording**.
- **Plausible Distractors** - for multiple-choice questions, incorrect answers must be plausible options.

### Bias/Fairness/Sensitivity Verifications

- **Avoids derogatory language, stereotype threats, and culturally specific colloquialisms.** Must not oversimplify or desensitize the experience of enslaved people.
- **Avoids offensive language or negative stereotypes related to gender identity or sexual orientation.**
- **Avoids negative religious portrayals and reliance on specific religious knowledge.**
- **Language must be accessible to the age group** and not portray any age group or individuals with disabilities in a negative manner.
- **Question should not demean people based on socioeconomic status** or suggest affluence is related to merit.

Out put a JSON list to specify if the test item follow the requirement and rationale, the format is:
{
    "requirements_check":[
        {
            "item": str, desc of the requriement
            "result": str, true or false
            "rationale": str, rationale of the result
        }
    ]
}

"""


CURRICULUM_VERIFICATION = """
Input the following test item:
{test_content}

Check how well does the test item cover the category and requirement:
category: {category},
requirement: {requirement}


Out put a JSON list to specify if the test item follow the requirement and rationale, the format is:
{
    "curriculum_check":[
        {
            "item": str, desc of the requriement
            "result": str, true or false
            "rationale": str, rationale of the result
        }
    ]
}

"""


CURRICULUM_GENERATION = """
Read the curriculum first and try summarize the learning objective category and its corresponding requirements.
And then extract the category and requirements. The output must be in valid JSON format:
```json
[
  {
    "category": "",
    "requirements": [
      "requirement description1",
      "requirement description2"
    ]
  }
]
```

Instructions:
* Only include curriculum content standards or learning objectives — the specific skills, knowledge, or competencies students are expected to learn.
* Exclude introductions, overviews, rationales, examples, notes, commentary, or “standards for practice” (e.g., habits of mind, thinking strategies, cross-disciplinary skills).
* Distill the category and make sure the number of category no more then 6.
* Distill the requirements and make sure the number of requirement no more then 6.
* Output clean, properly indented JSON only — no explanations or additional text.


The input curriculum:
{content}
"""

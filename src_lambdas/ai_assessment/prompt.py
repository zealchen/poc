TEST_GENERATION = """
Generate a new test item for the Massachusetts Comprehensive Assessment System (MCAS) based on the following specifications.

Subject: {subject}
Grade Level: {grade_level}
Content Standard: {}

Item Type: {item_type}

Bias and Sensitivity: Ensure the content is free of bias, stereotypes, and insensitive language. The scenario should be culturally appropriate and relatable to a diverse student population.

Factual Accuracy: If applicable, any factual information must be unequivocally correct. For science or history, provide a primary source reference document (e.g., a short text, a data table, an image) to be used with the item.

Universal Design: The question and all options/components must be clearly, precisely, and unambiguously worded, taking into consideration potential confusion for English learners.

Content Alignment: 
- **Passage Based** - A question must be associated with a high-quality reading passage.
- **Passage must be grade-appropriate** in word count, concepts, vocabulary, and readability.
- **Passage must be secured from copyright issues** only use public domain content.

Item Components:
1. Question Stem: Write a clear question or prompt for the student and be sure to include a passage if it is needed.
2. Correct Answer: Provide the single correct answer or the correct response, as well as a rationale for why it is correct.
3. Distractors (for selected-response items): Create three plausible but incorrect answer choices. Explain the reasoning behind each distractor (e.g., what common misconception or error it represents).

Output Json Format:
{
    "question_stem": str,
    "answer_choices": [str],
    "correct_answers": [str],
    "rationale_for_correct_answer": "str",
    "rationale_for_distractors": "str",
    "universal_design_considerations": "str",
}
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

Outout a JSON list to specify if the test item follow the requirement and rationale, the format is:
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
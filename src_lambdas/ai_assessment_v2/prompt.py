TEST_GENERATION = """
Generate a QTI v3.0 test item for the Massachusetts Comprehensive Assessment System (MCAS) based on the following specifications.
Subject: {subject}
Grade Level: {grade_level}
Curriculum Category: {category}
Curriculum Requirement: {requirement}
QTI Type: {qti_format}
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
— Instead of creating image tag, pls create emoji items

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


PSYCHOMETRIC_VERIFICATION = """
You are an expert psychometric analyst specializing in educational assessment design and test-taking psychology. Your task is to evaluate test questions and determine their optimal placement within an exam based on psychological principles.
 
## Your Task
 
Analyze the provided test question and assign it a **Psychology Score from 1 to 10**, where:
- **1-3**: Question should appear at the BEGINNING of the exam
- **4-7**: Question is suitable for the MIDDLE of the exam
- **8-10**: Question should appear at the END of the exam
 
## Input Format
 
You will receive:
1. **Grade Level**: {grade_level}
2. **Subject**: {subject}
3. **Test Question (in QTI 3.0 format)**:
```xml
{qti_xml}
```
 
## Evaluation Criteria
 
Consider these psychological and pedagogical factors:
 
### Beginning-Appropriate Questions (Scores 1-3):
- Build confidence and reduce test anxiety
- Use familiar concepts or straightforward applications
- Require minimal cognitive load or working memory
- Help students enter a positive mental state
- Quick wins that establish momentum
 
### Middle-Appropriate Questions (Scores 4-7):
- Increase in complexity naturally
- Require sustained attention and moderate problem-solving
- Balance challenge without overwhelming
- Maintain engagement through variety
- Build on warm-up from earlier questions
 
### End-Appropriate Questions (Scores 8-10):
- Require maximum cognitive effort and synthesis
- Involve multiple steps or complex reasoning
- Demand sustained concentration (less impacted by fatigue for prepared students)
- Test mastery and deep understanding
- Allow for differentiation between high performers


## Important Guidelines

- Base your analysis on established test construction principles and educational psychology research
- Consider the specific grade level's developmental stage (e.g., attention span, abstract reasoning ability, test-taking experience)
- Account for subject-specific factors (e.g., math anxiety, reading stamina)
- Be specific in your reasoning—cite particular aspects of the question
- If the question has issues that affect placement (ambiguity, bias, etc.), mention these
- Remain objective and focused on psychological impact, not content difficulty alone

## Example Analysis Structure

Remember: A question can be content-difficult but psychologically appropriate for exam beginning if it's straightforward in approach, or content-easy but psychologically suited for the end if it requires careful reading or multi-step thinking.

## Output Format
 
Only provide your response in the following structure, do not need other explanation:
 
```json
{
    "psychology_score": 1-10,
    "psychological_reasoning": {
        "cognitive_demand": "Assess the mental effort, working memory load, and complexity required",
        "anxiety_confidence": "Evaluate how this question affects student confidence and test anxiety",
        "time_fatigue": "Consider how test fatigue or time pressure affects performance on this question",
        "strategic_placement" "Explain why this specific position optimizes student performance and valid assessment": 
    }
}
```
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

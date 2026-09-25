FENCED = """```json
{
  "title": "Senior Data Engineer",
  "company": "Acme Corp",
  "location": "New York, NY",
  "remote": true,
  "years_experience_min": 7,
  "required_skills": ["Python", "Airflow", "AWS"]
}
```"""

WRONG_TYPES = """{
  "title": "Senior Data Engineer",
  "company": "Acme Corp",
  "location": "New York, NY",
  "remote": true,
  "years_experience_min": "7+",
  "required_skills": "Python, Airflow, AWS"
}"""

VALID = """{
  "title": "Senior Data Engineer",
  "company": "Acme Corp",
  "location": "New York, NY",
  "remote": true,
  "years_experience_min": 7,
  "required_skills": ["Python", "Airflow", "AWS"]
}"""

ALWAYS_BAD = """{"title": "x", "company": null}"""

PROSE = "Sure! Here's the extracted data for that job posting:"

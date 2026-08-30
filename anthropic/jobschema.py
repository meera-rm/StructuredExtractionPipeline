from pydantic import BaseModel, Field, ValidationError


class JobPosting(BaseModel):
    title: str = Field(description="The job title only, e.g. 'Senior Data Engineer'. Do not include the company name.")
    job_type: str
    location: str | None
    description: str
    salary: int
    responsibilities: list[str]
    qualifications: list[str]
    company_name: str | None = Field(description="Hiring company name, separate from the title.")
    years_experience_min: int | None = Field(description="Minimum years required, as a number, if stated anywhere in the text even as '7+ years'.")
    insurance: bool
    types_of_insurance: str
    required_skills: list[str] = Field(description="Concrete technologies only, e.g. 'python', 'airflow'. Do not include responsibilities or soft skills like 'production pipelines' or 'communication'.")


if __name__ == "__main__":
	good = {
		"title": "Senior Data Engineer",
		"job_type": "Full-time",
		"location": "New York, NY",
		"description": "We are looking for a Senior Data Engineer to join our team.",
		"salary": 120000,
		"responsibilities": ["Design and implement data pipelines", "Collaborate with data scientists"],
		"qualifications": ["Bachelor's degree in Computer Science", "5+ years of experience in data engineering"],
		"company_name": "Acme",
		"years_experience_min": 5,
		"insurance": True,
		"types_of_insurance": "Health, Dental, Vision",
		"required_skills": ["Python", "Airflow"]
	}

	print(JobPosting.model_validate(good))

	bad = dict(good, years_experience_min="5+")
	try:
		JobPosting.model_validate(bad)
	except ValidationError as e:
		print(e.json(indent=2))
	

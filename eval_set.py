
STXAVIER_TEXT = """
Medical Director
Forest Hills, NY
$145.00 - $160.00 Per Hour (Employer provided)

St. Xavier Community Services, Inc.
Location: Forest Hills, Queens, NY
Position Type: Part-Time or Full-Time (Negotiable)

About the Position
St. Xavier Community Services is seeking an experienced and dedicated
Medical Director to lead the medical operations of our Opioid Treatment
Program (OTP) located in Forest Hills, Queens. The Medical Director will
provide clinical leadership, oversight of medication-assisted treatment
(MAT) services, regulatory compliance, quality assurance, and supervision
of medical staff in accordance with OASAS, SAMHSA, DEA, and all applicable
federal and state regulations. Immediate Hire

Qualifications
* Doctor of Medicine (MD) or Doctor of Osteopathic Medicine (DO) degree
  from an accredited institution.
* Board Certified in Addiction Medicine or Addiction Psychiatry.
* Current unrestricted New York State Physician License.
* DEA Registration in good standing.
* Minimum of three (3) years of experience treating individuals with
  substance use disorders.
* Prior Opioid Treatment Program (OTP) experience strongly preferred.

Pay: $145.00 - $160.00 per hour
"""

JPM_TEXT = """
JPMorganChase
Lead Software Engineer, Platform & Experience Journeys

Hybrid
New York, NY, USA
Senior level

Lead platform engineering of reusable identity and onboarding components,
build automation for journey deployment, establish eventing and
observability, create developer-facing tools and migration tooling,
mentor engineers, and drive responsible adoption of AI-assisted
engineering practices and SDLC automation.

Required qualifications, capabilities and skills
* Formal training or certification on software engineering concepts and
  5+ years of applied experience.
* Experience designing or operating event-driven architectures using
  Kafka or equivalent messaging platforms.
* Experience building or maintaining CI/CD pipelines and deployment
  automation for secure, repeatable releases across environments.
* Experience using AI-assisted development tools and applying AI
  capabilities to build, test, improve, or operate software solutions.
* Experience with distributed tracing and observability across
  multi-service journey execution.
* Working knowledge of role-based access control, service ownership
  boundaries, and API contract design in distributed systems.
"""
EXAMPLES = [
    (
        """
        Senior Data Engineer - Acme Corp
        New York, NY (hybrid, 3 days onsite)

        We're hiring a Senior Data Engineer with 7+ years building
        production pipelines. You'll work in Python, Airflow, and AWS.
        Base salary 145,000 - 175,000 depending on experience.
        """,
        {
            "title": "Senior Data Engineer",
            "company": "Acme Corp",
            "remote": False,
            "years_experience_min": 7,
            "required_skills": ["python", "airflow", "aws"],
        },
    ),
    (
        """
        Junior Backend Developer (Remote)

        Join our fully remote team! No prior experience required --
        we train new grads. Familiarity with Python or Java a plus.
        """,
        {
            "title": "Junior Backend Developer",
            "company": None,
            "remote": True,
            "years_experience_min": 0,
            "required_skills": ["python", "java"],
        },
    ),
    (
        """
        Data Analyst - Northwind Traders

        Northwind Traders is looking for a Data Analyst with at least
        3 years of experience in SQL and Excel. This is an in-office
        role based in Chicago, IL.
        """,
        {
            "title": "Data Analyst",
            "company": "Northwind Traders",
            "remote": False,
            "years_experience_min": 3,
            "required_skills": ["sql", "excel"],
        },
    ),
    (
        """
        Staff Machine Learning Engineer

        10+ years of experience required. Fully remote position.
        Strong background in Python, PyTorch, and distributed training
        required. Company name withheld per client request.
        """,
        {
            "title": "Staff Machine Learning Engineer",
            "company": None,
            "remote": True,
            "years_experience_min": 10,
            "required_skills": ["python", "pytorch"],
        },
    ),

    (
        
        STXAVIER_TEXT,

        {
            "title": "Medical Director",
            # Two company names appear in the source (Glassdoor header vs
            # body text). Using the body text's self-identification as
            # ground truth.
            "company": "St. Xavier Community Services, Inc.",
            "remote": False,
            "years_experience_min": 3,
            # Non-tech role -- "skill" broadened to cover required
            # licenses/certifications per the widened field description.
            "required_skills": [
                "md or do degree",
                "board certified in addiction medicine",
                "dea registration",
                "ny state physician license",
            ],
        },
    ),
    (
        JPM_TEXT,
        {
            "title": "Lead Software Engineer, Platform & Experience Journeys",
            "company": "JPMorganChase",
            "remote": False,  # "Hybrid", not fully remote
            "years_experience_min": 5,
            "required_skills": ["kafka", "ci/cd", "api", "distributed tracing"],
        },
    ),
]
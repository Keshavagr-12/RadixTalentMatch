import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from docx import Document


SKILL_CATEGORIES = {
    # Programming Languages (COD)
    "Python": "COD",
    "C++": "COD",
    "Java": "COD",
    "JavaScript": "COD",
    "TypeScript": "COD",
    "C": "COD",
    "Go": "COD",
    "Rust": "COD",
    # Data Structures & Algorithms (DSA)
    "Data Structures and Algorithms": "DSA",
    "DSA": "DSA",
    # Object Oriented Design (OOD)
    "Object-Oriented Design": "OOD",
    "OOD": "OOD",
    "OOP": "OOD",
    # Operating Systems & Systems (OS)
    "Operating Systems": "OS",
    "Linux": "OS",
    "Multithreading": "OS",
    # Computer Networks (NETW)
    "Computer Networks": "NETW",
    "Networking": "NETW",
    # Databases & SQL (SQL)
    "SQL": "SQL",
    "PostgreSQL": "SQL",
    "MySQL": "SQL",
    # Software Engineering (SWE)
    "Software Engineering": "SWE",
    "FastAPI": "SWE",
    "API": "SWE",
    "Rate-limiter": "SWE",
    # Cloud & DevOps (CLOUD)
    "AWS": "CLOUD",
    "Docker": "CLOUD",
    "Kubernetes": "CLOUD",
    # AI & ML (AI)
    "Machine Learning": "AI",
    "Artificial Intelligence": "AI",
    # System Design (SYSD)
    "System Design": "SYSD",
    # Other tools & frameworks (OTHER)
    "Git": "OTHER",
    "Redis": "OTHER",
    "React": "OTHER",
    "Node.js": "OTHER",
    "MongoDB": "OTHER",
}


def read_resume_text(content: bytes, filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}")

    if extension == ".docx":
        try:
            document = Document(BytesIO(content))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise ValueError(f"Could not read DOCX: {exc}")

    raise ValueError("Only PDF and DOCX files are supported.")


def _matches_skill(text: str, skill_name: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(skill_name.lower()) + r"(?!\w)"
    return bool(re.search(pattern, text.lower()))


def extract_resume_data(content: bytes, filename: str) -> dict:
    text = read_resume_text(content, filename)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        raise ValueError(
            "No readable text found in the resume. "
            "The PDF may be scanned or image-based."
        )

    data = {}

    # Extract email only when it exists in the resume.
    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )
    if email_match:
        data["email"] = email_match.group(0).lower()

    # Usually, the candidate's name is near the beginning.
    first_line = re.sub(r"^[•\-\s]+", "", lines[0]).strip()
    if (
        len(first_line) <= 100
        and not re.search(r"@|https?://|www\.", first_line, re.I)
        and not re.search(
            r"\b(resume|curriculum vitae|education|technical skills|projects)\b",
            first_line,
            re.I,
        )
    ):
        data["name"] = first_line

    # Extract skills using known terms with word boundaries to prevent false positives
    skills = []
    seen_skills = set()

    for skill_name, category_code in SKILL_CATEGORIES.items():
        canonical_key = skill_name.lower()
        if canonical_key in seen_skills:
            continue

        if _matches_skill(text, skill_name):
            # Check for acronym alias overlap (e.g., skip DSA if already added Data Structures and Algorithms)
            if skill_name == "DSA" and "data structures and algorithms" in seen_skills:
                continue
            if skill_name in ("OOD", "OOP") and "object-oriented design" in seen_skills:
                continue

            evidence = "Listed in resume"
            for line in lines:
                if _matches_skill(line, skill_name):
                    evidence = line[:200]
                    break

            skills.append({
                "skill_name": skill_name,
                "category_code": category_code,
                "evidence": evidence,
                "confidence": "medium",
            })
            seen_skills.add(canonical_key)

    if skills:
        data["skills"] = skills

    # Extract education when a degree is explicitly mentioned.
    education = []
    degree_pattern = re.compile(
        r"\b(B\.?\s?Tech|B\.?\s?E\.?|M\.?\s?Tech|"
        r"M\.?\s?E\.?|B\.?\s?Sc|M\.?\s?Sc|"
        r"Bachelor(?:'s)?|Master(?:'s)?)\b",
        re.I,
    )

    for line in lines:
        if degree_pattern.search(line):
            year_match = re.search(r"\b(?:19|20)\d{2}\b", line)
            field = None

            if re.search(r"computer science", line, re.I):
                field = "Computer Science and Engineering"

            education.append({
                "degree": line,
                "institution": "Not specified",
                "graduation_year": (
                    int(year_match.group(0)) if year_match else None
                ),
                "field_of_study": field,
            })
            break

    if education:
        data["education"] = education

    # Section header check pattern
    is_header = re.compile(
        r"^(hackathons?|competitions?|internships?|work experience|experience|"
        r"projects?|education|skills?|certifications?)(\s*[/&,]\s*"
        r"(hackathons?|competitions?|internships?|work experience|experience|"
        r"projects?|education|skills?|certifications?))*\s*:?$",
        re.I,
    )

    # Extract hackathon details from matching resume lines.
    hackathons = []
    for line in lines:
        if is_header.match(line):
            continue
        if re.search(r"hackathon", line, re.I):
            year_match = re.search(r"\b(20\d{2})\b", line)
            ach_match = re.search(
                r"\b(winner|runner[- ]?up|finalist|\d+(?:st|nd|rd|th)\s+place)\b",
                line,
                re.I,
            )
            hackathons.append({
                "name": line,
                "achievement": ach_match.group(0).capitalize() if ach_match else None,
                "year": int(year_match.group(1)) if year_match else None,
            })

    if hackathons:
        data["hackathons"] = hackathons

    # Extract internship information from matching lines.
    internships = []
    for line in lines:
        if is_header.match(line):
            continue
        if re.search(r"\bintern(ship)?\b", line, re.I):
            internships.append({
                "company": "Not specified",
                "role": "Intern",
                "description": line,
                "duration": None,
            })

    if internships:
        data["internships"] = internships

    # Extract preferred roles when a preferred-roles section exists.
    preferred_roles = []
    in_roles_section = False

    for line in lines:
        colon_match = re.match(r"preferred roles?\s*:\s*(.*)$", line, re.I)
        if colon_match:
            inline_roles = colon_match.group(1).strip()
            if inline_roles:
                preferred_roles.extend(
                    role.strip(" •,-")
                    for role in re.split(r"[,|/]", inline_roles)
                    if role.strip(" •,-")
                )
            else:
                in_roles_section = True
            continue

        if re.match(r"preferred roles?\s*$", line, re.I):
            in_roles_section = True
            continue

        if in_roles_section:
            if re.match(
                r"(education|technical skills|projects|"
                r"certifications|achievements|experience|skills|hackathons)\b",
                line,
                re.I,
            ):
                break

            preferred_roles.extend(
                role.strip(" •,-")
                for role in re.split(r"[,|/]", line)
                if role.strip(" •,-")
            )

    if preferred_roles:
        data["preferred_roles"] = preferred_roles

    return {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "education": data.get("education", []),
        "skills": data.get("skills", []),
        "hackathons": data.get("hackathons", []),
        "internships": data.get("internships", []),
        "certifications": data.get("certifications", []),
        "preferred_roles": data.get("preferred_roles", []),
        "cv_file": None,
    }

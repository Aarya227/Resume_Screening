from sentence_transformers import SentenceTransformer, util
import numpy as np
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

SKILLS_DB = [
    "Python", "Java", "C++", "C", "SQL", "MongoDB", "PostgreSQL",
    "JavaScript", "Node.js", "Express.js", "React", "HTML", "CSS",
    "Flask", "Django", "Machine Learning", "Deep Learning", "Data Analysis",
    "AWS", "Azure", "GCP", "Git", "Excel"
]

# ---------------- Resume Matching ---------------- #
def match_job_to_candidates(job_text, candidate_texts, top_k=5):
    if not candidate_texts:
        return []

    job_vec = model.encode(job_text, convert_to_tensor=True)
    cand_vecs = model.encode(candidate_texts, convert_to_tensor=True)
    cosines = util.cos_sim(job_vec, cand_vecs).cpu().numpy().flatten()

    job_skills = [s.lower() for s in SKILLS_DB if s.lower() in job_text.lower()]

    results = []
    for i, score in enumerate(cosines):
        scaled_score = score * 10
        resume_lower = candidate_texts[i].lower()
        matched_skills = [s for s in job_skills if s in resume_lower]

        if job_skills:
            skill_match_ratio = len(matched_skills) / len(job_skills)
            if skill_match_ratio >= 0.6:
                scaled_score = max(scaled_score, 7.5)
            elif skill_match_ratio >= 0.4:
                scaled_score = max(scaled_score, 6.0)

        results.append((i, round(float(scaled_score), 2)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

# ---------------- Resume Suggestions ---------------- #
def suggest_improvements(job_text, resume_text):
    suggestions = []

    job_words = set([w.lower() for w in re.findall(r"\w+", job_text)])
    resume_lower = resume_text.lower()

    missing_skills = [s for s in SKILLS_DB if s.lower() in job_words and s.lower() not in resume_lower]
    if missing_skills:
        suggestions.append(f"Consider adding skills like: {', '.join(missing_skills[:5])}")

    if "@" not in resume_text:
        suggestions.append("Add a professional email address.")
    if not re.search(r"\+?\d[\d\s-]{8,}\d", resume_text):
        suggestions.append("Include a valid phone number.")
    if not re.search(r"\d+\s*(years|year|months|month)", resume_lower):
        suggestions.append("Mention work experience clearly (e.g., '2 years in backend development').")

    if not suggestions:
        suggestions.append("Resume is well-aligned with the job description.")

    return suggestions

import re
import spacy

# Load spaCy model (make sure en_core_web_sm is installed)
nlp = spacy.load("en_core_web_sm")

# Skills database (keep in sync with matcher.py)
SKILLS_DB = [
    "Python", "Java", "C++", "C", "SQL", "MongoDB", "PostgreSQL",
    "JavaScript", "Node.js", "Express.js", "React", "HTML", "CSS",
    "Flask", "Django", "Machine Learning", "Deep Learning", "Data Analysis",
    "AWS", "Azure", "GCP", "Git", "Excel"
]

# Degree patterns and a numeric priority (higher -> more advanced)
DEGREE_PATTERNS = [
    (r"\bph\.?d\b|\bdoctorate\b", "PhD", 7),
    (r"\bm\.?tech\b|\bmtech\b|\bmaster\b|\bm\.?s\b|\bms\b|\bm\.?sc\b|\bmsc\b", "Master", 6),
    (r"\bmca\b", "MCA", 6),
    (r"\bmba\b", "MBA", 6),
    (r"\bb\.?tech\b|\bbtech\b|\bb\.?e\b|\bbe\b|\bbachelor\b|\bb\.?sc\b|\bbsc\b", "Bachelor", 5),
    (r"\bdiploma\b", "Diploma", 4),
    (r"\b12th\b|\bhigher secondary\b|\bsenior secondary\b", "Higher Secondary", 2),
    (r"\b10th\b|\bsecondary\b", "Secondary", 1),
]

# helper: sanitize whitespace
def _clean(line: str) -> str:
    return " ".join(line.split()).strip()

# ---------- Name Extraction ----------
def extract_name(resume_text: str) -> str:
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    # heuristic: top 6 lines, prefer a short line (2-4 words) without emails/urls/digits
    for line in lines[:6]:
        if (2 <= len(line.split()) <= 4
            and not re.search(r"[@\d]|www\.|http", line, re.I)
            and re.search(r"[A-Z]", line)):
            # also avoid typical headings
            if not re.search(r"resume|curriculum vitae|curriculum|cv", line, re.I):
                return _clean(line)
    # fallback: use spaCy PERSON entity on top lines
    doc = nlp(" ".join(lines[:8]))
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return _clean(ent.text)
    return "Not Found"

# ---------- Email Extraction ----------
def extract_email(resume_text: str) -> str:
    email = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
    return email[0].strip() if email else "Not Found"

# ---------- Phone Extraction ----------
def extract_phone(resume_text: str) -> str:
    # Accepts +91, +1, (), -, spaces etc.
    phones = re.findall(r"(\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5})", resume_text)
    if phones:
        # pick the longest/most complete-looking match
        phones = [p.strip() for p in phones]
        phones.sort(key=lambda x: len(re.sub(r"\D", "", x)), reverse=True)
        return phones[0]
    return "Not Found"

# ---------- Skills Extraction ----------
def extract_skills(resume_text: str, jd_text: str = "") -> list:
    resume_lower = resume_text.lower()
    found = []
    for skill in SKILLS_DB:
        # match whole words (case-insensitive)
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", resume_lower):
            found.append(skill)
    return sorted(list(set(found))) if found else []

# ---------- Education Extraction (robust) ----------
def _find_years(text: str):
    """Return (start_year, end_year) if found; end_year may be None."""
    # year range first
    m = re.search(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", text)
    if m:
        # m.group(0) is the full range; extract numbers
        yrs = re.findall(r"(?:19|20)\d{2}", m.group(0))
        if len(yrs) >= 2:
            return (int(yrs[0]), int(yrs[1]))
    # single year occurrences
    years = re.findall(r"\b(19|20)\d{2}\b", text)
    if years:
        # return the last year seen (likely graduation)
        all_years = re.findall(r"\b(?:19|20)\d{2}\b", text)
        if all_years:
            y = int(all_years[-1])
            return (None, y)
    return (None, None)

def extract_education(resume_text: str) -> str:
    """
    Scan the resume text for education-related lines, extract candidate entries,
    rank them (by degree priority and end-year), and return a nicely formatted single sentence.
    """
    lines = [_clean(l) for l in resume_text.splitlines() if l.strip()]
    candidates = []

    for idx, line in enumerate(lines):
        l_low = line.lower()
        # consider line if it contains degree keywords or 'university/college/institute' or a year
        if (any(re.search(pat, l_low, re.I) for pat,_,_ in [(p,_,_) for p,_,_ in DEGREE_PATTERNS])
            or re.search(r"\b(university|college|institute|school|academy|institute of technology|iim|iit|nit|iiit|bits)\b", l_low, re.I)
            or re.search(r"(?:19|20)\d{2}", l_low)):
            # attempt to find degree and level
            degree_label = None
            degree_level = 0
            for pat, label, level in DEGREE_PATTERNS:
                if re.search(pat, line, re.I):
                    degree_label = label
                    degree_level = level
                    break

            # extract field after 'in' or 'of' (best-effort)
            field = ""
            fmatch = re.search(r"(?:in|of|majoring in|specialization|specialisation|specialization:)\s+([A-Za-z0-9 &\.\-+]+?)(?:,|\(| at | from | - |$)", line, re.I)
            if fmatch:
                field = _clean(fmatch.group(1))

            # extract institution (look for University/College/Institute etc.)
            inst = ""
            inst_match = re.search(r"([A-Za-z0-9 &\.\-]+(?:University|College|Institute|School|IIT|NIT|IIIT|IIM|BITS|VIT|SPIT|PES|SRM|COEP)[A-Za-z0-9 &\.\-]*)", line, re.I)
            if inst_match:
                inst = _clean(inst_match.group(0))
            else:
                # fallback: after 'at' or 'from' or after dash
                alt = re.search(r"(?:at|from)\s+([A-Za-z0-9 &\.\-]+)", line, re.I)
                if alt:
                    inst = _clean(alt.group(1).split(",")[0])

            # years
            start_y, end_y = _find_years(line)

            candidates.append({
                "line": line,
                "idx": idx,
                "degree_label": degree_label,
                "degree_level": degree_level,
                "field": field,
                "institution": inst,
                "start_year": start_y,
                "end_year": end_y
            })

    # If nothing found, try to find multi-line education blocks (two-line patterns)
    if not candidates:
        for i in range(len(lines)-1):
            block = lines[i] + " " + lines[i+1]
            if re.search(r"(university|college|institute|b\.?tech|mba|bachelor|master|ph\.?d|diploma)", block, re.I):
                # reuse same parsing on block
                start_y, end_y = _find_years(block)
                inst_match = re.search(r"([A-Za-z0-9 &\.\-]+(?:University|College|Institute|School|IIT|NIT|IIIT|IIM|BITS)[A-Za-z0-9 &\.\-]*)", block, re.I)
                inst = _clean(inst_match.group(0)) if inst_match else ""
                field_match = re.search(r"(?:in|of)\s+([A-Za-z0-9 &\.\-]+?)(?:,| at | from | - |$)", block, re.I)
                field = _clean(field_match.group(1)) if field_match else ""
                deg = None
                deg_level = 0
                for pat, label, level in DEGREE_PATTERNS:
                    if re.search(pat, block, re.I):
                        deg = label
                        deg_level = level
                        break
                candidates.append({
                    "line": block,
                    "idx": i,
                    "degree_label": deg,
                    "degree_level": deg_level,
                    "field": field,
                    "institution": inst,
                    "start_year": start_y,
                    "end_year": end_y
                })

    if not candidates:
        return "Not Found"

    # Rank candidates: primary by degree_level, then by end_year (descending), then by index (earlier)
    def cand_score(c):
        # degree_level is most important; missing level get 0
        lvl = c.get("degree_level", 0) or 0
        endy = c.get("end_year") or 0
        # score tuple
        return (lvl, endy, -c.get("idx", 0))

    candidates.sort(key=cand_score, reverse=True)
    best = candidates[0]

    # Build formatted sentence
    parts = []
    deg = best.get("degree_label")
    if deg:
        parts.append(deg)
    # if field exists:
    fld = best.get("field")
    if fld:
        # remove trailing words like 'PES University' accidentally captured in field
        # if field includes 'University' assume it's institution; move to inst if inst empty
        if "university" in fld.lower() or "college" in fld.lower() or "institute" in fld.lower():
            if not best.get("institution"):
                best["institution"] = fld
            else:
                # ignore field, it's actually inst
                fld = ""
        else:
            parts.append(f"in {fld}")

    inst = best.get("institution")
    if inst:
        parts.append(f"at {inst}")

    # years
    sy, ey = best.get("start_year"), best.get("end_year")
    if ey and sy:
        parts.append(f"({sy}\u2013{ey})")  # en-dash
    elif ey:
        parts.append(f"({ey})")

    formatted = " ".join(parts).strip()
    if not formatted:
        # fallback: use the raw line cleaned up
        formatted = _clean(best.get("line", ""))

    return formatted

# ---------- Main Parse Function ----------
def parse_resume(resume_text: str, jd_text: str = "") -> dict:
    return {
        "name": extract_name(resume_text),
        "email": extract_email(resume_text),
        "phone": extract_phone(resume_text),
        "skills": extract_skills(resume_text, jd_text),
        "education": extract_education(resume_text),
    }

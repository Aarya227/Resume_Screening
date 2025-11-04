from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import docx2txt
import pdfplumber
import zipfile
from resume_parser import parse_resume
from matcher import match_job_to_candidates, suggest_improvements

app = Flask(**name**)
app.secret_key = "change_this_to_a_random_secret_in_production"

FAKE_USERNAME = "admin"
FAKE_PASSWORD = "password123"

# ---------- Text Extraction ----------

def extract_text(file_path):
text = ""
if file_path.endswith(".pdf"):
try:
with pdfplumber.open(file_path) as pdf:
for page in pdf.pages:
text += page.extract_text() or ""
except Exception:
from PyPDF2 import PdfReader
reader = PdfReader(file_path)
for page in reader.pages:
text += page.extract_text() or ""

```
elif file_path.endswith(".docx"):
    text = docx2txt.process(file_path) or ""

elif file_path.endswith(".txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read() or ""
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            text = f.read() or ""
return text
```

# ---------- Authentication helpers ----------

def login_required(fn):
from functools import wraps
@wraps(fn)
def wrapper(*args, **kwargs):
if not session.get("logged_in"):
return redirect(url_for("login", next=request.path))
return fn(*args, **kwargs)
return wrapper

# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
if request.method == "POST":
username = request.form.get("username", "").strip()
password = request.form.get("password", "").strip()
if username == FAKE_USERNAME and password == FAKE_PASSWORD:
session["logged_in"] = True
session["username"] = username
next_url = request.args.get("next") or url_for("index")
flash("Logged in successfully.", "success")
return redirect(next_url)
else:
flash("Invalid username or password.", "danger")
return render_template("login.html", username=username)
else:
return render_template("login.html")

@app.route("/logout")
def logout():
session.clear()
flash("Logged out.", "info")
return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
return render_template("index.html", username=session.get("username"))

@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
os.makedirs("uploads", exist_ok=True)

```
jd_text = request.form.get("jd_text", "")
jd_file = request.files.get("jd_file")
if jd_file and jd_file.filename != "":
    jd_path = os.path.join("uploads", jd_file.filename)
    jd_file.save(jd_path)
    jd_text += "\n" + extract_text(jd_path)

resumes_raw = []
resumes_info = []

zip_file = request.files.get("zip_file")
if zip_file and zip_file.filename != "":
    zip_path = os.path.join("uploads", zip_file.filename)
    zip_file.save(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("uploads/")
        for filename in zip_ref.namelist():
            file_path = os.path.join("uploads", filename)
            if filename.lower().endswith((".pdf", ".docx", ".txt")):
                text = extract_text(file_path)
                resumes_raw.append(text)
                info = parse_resume(text, jd_text)
                info["FileName"] = filename
                resumes_info.append(info)

single_file = request.files.get("file")
if single_file and single_file.filename != "" and not resumes_raw:
    filepath = os.path.join("uploads", single_file.filename)
    single_file.save(filepath)
    text = extract_text(filepath)
    resumes_raw.append(text)
    info = parse_resume(text, jd_text)
    info["FileName"] = single_file.filename
    resumes_info.append(info)

matches = match_job_to_candidates(jd_text, resumes_raw, top_k=len(resumes_raw))

for idx, score in matches:
    if 0 <= idx < len(resumes_info):
        resumes_info[idx]["Score"] = score
        resumes_info[idx]["Suggestions"] = suggest_improvements(jd_text, resumes_raw[idx])

# Removed rendering of extracted job description
return render_template("results.html", resumes_info=resumes_info, username=session.get("username"))
```

if **name** == "**main**":
app.run(debug=True)

# 🎓 BBDNIIT Online Examination Platform

![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-CONTAINERIZED-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![AI Proctoring](https://img.shields.io/badge/AI%20PROCTORING-ENABLED-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/LICENSE-EDUCATIONAL-7E57C2?style=for-the-badge)

---

**A college-grade, AI-proctored online examination system** built with Django 4.2, TailwindCSS, and
modern web technologies — capable of handling 100–200 concurrent students.

---

## LIVE URL :https://college-exam-platform-1.onrender.com/

---

## 🚀 Quick Start (Local — SQLite)

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Unzip and enter the project
unzip bbdniit_exam.zip
cd bbdniit_exam

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create a superuser (admin)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## 🐳 Docker Deployment (PostgreSQL + Redis)

```bash
# 1. Copy and edit environment variables
cp .env.example .env
# Edit .env with your SECRET_KEY, DB credentials, etc.

# 2. Build and start
docker-compose up --build -d

# 3. Run migrations inside the container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

App will be available at **http://localhost:8000**

---

## 🏗️ Project Structure

```
bbdniit_exam/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── onlinexam/               # Django project config
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── base.py          # Shared settings
│       ├── development.py   # SQLite, DEBUG=True
│       └── production.py    # PostgreSQL, DEBUG=False
│
├── exam/                    # Core exam app
│   ├── models.py            # AcademicCourse, Subject, Course, Question, Result, ProctoringAlert
│   ├── views.py             # Admin views
│   ├── forms.py
│   └── services/
│       └── question_parser.py   # AI-ready parser (CSV/JSON/PDF/DOCX)
│
├── teacher/                 # Teacher portal
│   ├── models.py
│   ├── views.py             # Full control panel
│   └── urls.py
│
├── student/                 # Student portal
│   ├── models.py
│   ├── views.py             # Exam flow + proctoring
│   └── urls.py
│
├── templates/               # All HTML templates (TailwindCSS)
│   ├── base.html
│   ├── exam/
│   ├── teacher/
│   └── student/
│
└── static/                  # Static assets
```

---

## 👥 User Roles

| Role    | Access                                                      |
|---------|-------------------------------------------------------------|
| Admin   | Full system control, manage teachers/students/courses       |
| Teacher | Create exams, add questions, upload files, view results     |
| Student | Attempt exams, view results                                 |

### Login URLs
- **Admin:** `/adminlogin`
- **Teacher:** `/teacher/teacherlogin`
- **Student:** `/student/studentlogin`

---

## ✨ Features

### Academic Hierarchy
- **Programmes** (BCA, MCA, B.Tech…) → **Subjects** → **Exams**

### Exam Management
- Create exams with: subject, duration, time window (start/end), max attempts
- Upload questions via **CSV or JSON** (auto-imported)
- Upload **PDF/DOCX** (stored for future AI parsing)
- Upload **answer key** separately
- Edit or delete exams (delete blocked if results exist)

### Student Experience
- **Instruction screen** with: course, subject, questions count, attempts, time slot, watermark
- **Distraction-free exam screen** with fixed timer top-right
- Answers auto-saved via cookies

### Proctoring System
| Feature | Limit | Action |
|---------|-------|--------|
| Tab/window switch | > 4 | Auto-submit |
| Face not detected | > 4 | Auto-submit |
| Timer expires | — | Auto-submit |
| All violations | — | Logged to DB |

### Attempt Restriction
- Students **cannot re-attempt the same exam on the same day**

### Results & Grades
| Percentage | Grade |
|-----------|-------|
| ≥ 90% | A+ |
| ≥ 75% | A |
| ≥ 60% | B |
| ≥ 45% | C |
| ≥ 33% | D |
| < 33% | F |

---

## 📥 Question Import Format

### CSV (`questions.csv`)
```csv
question,option1,option2,option3,option4,answer,marks
"What is 2+2?","1","2","4","5","Option3",1
"Capital of India?","Mumbai","Delhi","Chennai","Kolkata","Option2",2
```

### JSON (`questions.json`)
```json
[
  {
    "question": "What is 2+2?",
    "option1": "1", "option2": "2", "option3": "4", "option4": "5",
    "answer": "Option3",
    "marks": 1
  }
]
```
Upload via: **Teacher → View Exams → Upload Quiz**

---

## ⚙️ Environment Variables (`.env`)

```env
DJANGO_ENV=development
SECRET_KEY=your-secret-key-here
DB_NAME=bbdniit_exam
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
EMAIL_RECEIVING_USER=admin@email.com
```

---

## 🏭 Production with Gunicorn

```bash
DJANGO_ENV=production gunicorn onlinexam.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread \
  --timeout 120
```

Recommended: Put **Nginx** in front of Gunicorn as a reverse proxy.

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 |
| Frontend | TailwindCSS (CDN) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Cache | LocMemCache (dev) / Redis (prod) |
| Server | Gunicorn |
| Proctoring | Browser JS (camera + visibility API) |
| Containerisation | Docker + docker-compose |

---

## 📝 License
© BBDNIIT — For educational use only.

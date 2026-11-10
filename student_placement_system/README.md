# CareerBridge – Student Placement and Recruitment Management System

## Stack
Python 3.12, Django 5.2, MySQL, Bootstrap 5, HTML, CSS, JavaScript.

## Windows installation
1. Install Python 3.12 and MySQL Server.
2. Open this folder in VS Code.
3. Run:
```powershell
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
4. Create database in MySQL:
```sql
CREATE DATABASE placement_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
5. Copy `.env.example` to `.env`; enter DB password and SMTP credentials.
6. Run:
```powershell
python manage.py makemigrations placement
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
7. Open http://127.0.0.1:8000/

## Main routes
`/` home · `/register/` registration · `/login/` login · `/dashboard/` student dashboard · `/profile/` profile · `/jobs/` jobs · `/applications/` student applications · `/placement-admin/` admin dashboard · `/django-admin/` Django admin.

## Features
Student registration and unique email/registration number checks; pending admin approval; activation email with one-time password setup; login lock after 3 failed attempts for 30 minutes; profile and resume validation (PDF/DOCX, max 5 MB); company and job creation; rule-based eligibility; database-level duplicate application prevention; application status updates and notifications.

## Email
For Gmail, enable 2-Step Verification and create a Google App Password. Put it in `EMAIL_HOST_PASSWORD`. Never put your normal Gmail password or `.env` file in GitHub.

## Important MVP limitations
This is a functional starter/MVP, not a production-hardened recruitment service. Company self-service accounts, saved jobs, full multi-record education/project/certification forms, interview calendar, report exports and automated test coverage are not yet implemented. The eligibility score compares CGPA with minimum CGPA; do not enter percentage thresholds into that field. The application resume field references the uploaded profile file; a production system should create an immutable copy and protect document downloads. Before deployment, add malware scanning, HTTPS, secure production settings, backups, rate limiting and security testing.

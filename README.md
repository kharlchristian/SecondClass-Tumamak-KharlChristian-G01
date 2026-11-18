# SecondClass

SecondClass is a Django-rendered campus marketplace for students buying and selling used textbooks organized by course. It includes account registration, authentication, role-specific dashboards, profile editing, and a textbook listing vertical slice for creating, browsing, updating, deleting, and moderating listings.

## Requirements

- Python 3.12 or newer
- PostgreSQL 14 or newer

SQLite is not used by the application. Django's default database is PostgreSQL; the separate in-memory SQLite configuration is only for running the automated tests without a PostgreSQL service.

## Local setup

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create a PostgreSQL database and user, then copy `.env.example` to `.env`. Set the database values and generate a private Django key:

   ```powershell
   Copy-Item .env.example .env
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Put the generated value in `DJANGO_SECRET_KEY` in `.env`. Never commit `.env`; it is ignored by Git.

4. Apply migrations and create an administrator:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

   A superuser is assigned the `ADMIN` role. New registrations receive the `STUDENT` role.

5. Start the development server:

   ```powershell
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/`. Administrators can use the custom panel at `/admin/`.

## Account feature

- Registration validates required fields, email format, case-insensitive username/email uniqueness, and matching passwords. Django password validators run before the password is hashed.
- Login uses email and password; logout is a CSRF-protected POST that ends the session.
- Students and administrators are redirected to separate dashboards. Direct access to the other role's dashboard is denied.
- Signed-in users can view and update only their own name, email, and contact number at `/profile/`.

## Textbook listings

- Students can create, browse, filter by course/subject/edition/condition/price, update, and delete textbook listings.
- Each listing is linked to its student seller and a course. Prices must be positive; title, edition, and condition are required.
- Listing prices are entered and displayed in Philippine pesos (PHP).
- Sellers can change status between available, reserved, and sold. Sold or removed listings cannot be returned to an active status, and each seller may have at most 20 active listings.
- Administrators can remove listings and maintain course references in the custom admin panel.
- The initial migration seeds these placeholder course options, which administrators can update in the custom admin panel:
  - `CSIT321` — Applications Development and Emerging Technologies
  - `CSIT340` — Industry Elective 1
  - `IT365` — Data Analytics 1
  - `CSIT212` — Quantitative Methods
  - `CSIT284` — Platform-based Development 3 (Mobile)
  - `CSIT227` — Object-oriented Programming1
  - `CSIT228` — Object-oriented Programming 2
  - `CSIT111` — Introduction to Computing

Apply the new marketplace migrations with `python manage.py migrate` as part of the local setup.

## Tests

Run the account and marketplace tests using the test-only settings module:

```powershell
python manage.py test accounts marketplace --settings=config.test_settings
```

The test settings use an in-memory SQLite database only for automated tests; normal application settings always use PostgreSQL.

If PostgreSQL is not available for a local preview, you can use a temporary SQLite database with the test-only settings. This is only for previewing and is not the application's PostgreSQL setup:

```powershell
$env:DJANGO_TEST_DATABASE = (Join-Path (Get-Location) "db.sqlite3")
python manage.py migrate --settings=config.test_settings
python manage.py runserver --settings=config.test_settings
```

In another PowerShell window using the same `.venv`, run account tests without setting `DJANGO_TEST_DATABASE` to keep their database in memory:

```powershell
python manage.py test accounts --settings=config.test_settings
```

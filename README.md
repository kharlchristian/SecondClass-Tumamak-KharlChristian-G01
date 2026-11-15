# SecondClass

SecondClass is a Django-rendered campus marketplace for students buying and selling used textbooks organized by course. The initial milestone implements account registration, authentication, role-specific dashboards, and profile editing for the SDD's `STUDENT` and `ADMIN` roles.

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

   Visit `http://127.0.0.1:8000/`. Admin users can also access `/admin/`.

## Account feature

- Registration validates required fields, email format, case-insensitive username/email uniqueness, and matching passwords. Django password validators run before the password is hashed.
- Login uses email and password; logout is a CSRF-protected POST that ends the session.
- Students and administrators are redirected to separate dashboards. Direct access to the other role's dashboard is denied.
- Signed-in users can view and update only their own name, email, and contact number at `/profile/`.

## Tests

Run the account tests using the test-only settings module:

```powershell
python manage.py test accounts --settings=config.test_settings
```

The test settings use an in-memory SQLite database only for automated tests; normal application settings always use PostgreSQL.

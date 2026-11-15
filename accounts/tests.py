from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import RegistrationForm


User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_creates_student_with_hashed_password_and_success_message(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "TextbookFan",
                "email": "Student@Example.com",
                "full_name": "A Student",
                "password1": "Uncommon-book-password-384!",
                "password2": "Uncommon-book-password-384!",
            },
            follow=True,
        )

        user = User.objects.get(email="student@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse("accounts:login"), 302)])
        self.assertEqual(user.username, "textbookfan")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password("Uncommon-book-password-384!"))
        self.assertNotEqual(user.password, "Uncommon-book-password-384!")
        self.assertContains(response, "Your account has been created")

    def test_registration_rejects_case_insensitive_duplicate_username_or_email(self):
        User.objects.create_user(
            email="existing@example.com",
            username="existing",
            password="Uncommon-book-password-384!",
            full_name="Existing Student",
        )

        for username, email in (
            ("EXISTING", "new@example.com"),
            ("newstudent", "EXISTING@example.com"),
        ):
            form = RegistrationForm(
                data={
                    "username": username,
                    "email": email,
                    "full_name": "New Student",
                    "password1": "Uncommon-book-password-384!",
                    "password2": "Uncommon-book-password-384!",
                }
            )
            self.assertFalse(form.is_valid())

    def test_registration_rejects_mismatched_passwords(self):
        form = RegistrationForm(
            data={
                "username": "newstudent",
                "email": "new@example.com",
                "full_name": "New Student",
                "password1": "Uncommon-book-password-384!",
                "password2": "Different-book-password-384!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_registration_requires_fields_and_a_valid_email(self):
        missing_fields_form = RegistrationForm(
            data={
                "username": "",
                "email": "",
                "full_name": "",
                "password1": "Uncommon-book-password-384!",
                "password2": "Uncommon-book-password-384!",
            }
        )
        self.assertFalse(missing_fields_form.is_valid())
        self.assertTrue({"username", "email", "full_name"}.issubset(missing_fields_form.errors))

        invalid_email_form = RegistrationForm(
            data={
                "username": "newstudent",
                "email": "not-an-email",
                "full_name": "New Student",
                "password1": "Uncommon-book-password-384!",
                "password2": "Uncommon-book-password-384!",
            }
        )
        self.assertFalse(invalid_email_form.is_valid())
        self.assertIn("email", invalid_email_form.errors)


class AccountAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            username="student",
            password="Uncommon-book-password-384!",
            full_name="Test Student",
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="Uncommon-admin-password-384!",
            full_name="Test Admin",
        )

    def test_dashboard_redirects_by_role_and_blocks_other_dashboard(self):
        self.client.force_login(self.student)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("accounts:student_dashboard"))
        self.assertRedirects(self.client.get(reverse("accounts:admin_dashboard")), reverse("accounts:student_dashboard"))

        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("accounts:admin_dashboard"))
        self.assertRedirects(self.client.get(reverse("accounts:student_dashboard")), reverse("accounts:admin_dashboard"))

    def test_protected_pages_redirect_anonymous_users_to_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

    def test_profile_edit_changes_only_the_signed_in_user(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "full_name": "Updated Student",
                "email": "updated@example.com",
                "contact_number": "09171234567",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.student.refresh_from_db()
        self.assertEqual(self.student.full_name, "Updated Student")
        self.assertEqual(self.student.email, "updated@example.com")
        self.assertEqual(self.student.contact_number, "09171234567")

    def test_login_and_logout_manage_the_session(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "STUDENT@EXAMPLE.COM", "password": "Uncommon-book-password-384!"},
        )
        self.assertRedirects(response, reverse("accounts:student_dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin@example.com", "password": "Uncommon-admin-password-384!"},
        )
        self.assertRedirects(response, reverse("accounts:admin_dashboard"))

    def test_invalid_login_shows_a_clear_error(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "student@example.com", "password": "incorrect"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct email and password.")

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Course, Listing


User = get_user_model()


class ListingWorkflowTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            username="seller",
            password="Uncommon-book-password-384!",
            full_name="Textbook Seller",
        )
        self.other_student = User.objects.create_user(
            email="buyer@example.com",
            username="buyer",
            password="Uncommon-book-password-384!",
            full_name="Textbook Buyer",
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="Uncommon-admin-password-384!",
            full_name="Platform Admin",
        )
        self.course, _ = Course.objects.update_or_create(
            course_code="CSIT327",
            defaults={
                "course_name": "Information Management 2",
                "subject": "Information Systems",
            },
        )
        self.other_course = Course.objects.create(
            course_code="MATH210",
            course_name="Applied Mathematics",
            subject="Mathematics",
        )

    def create_listing(self, **overrides):
        values = {
            "seller": self.seller,
            "course": self.course,
            "title": "Database Systems",
            "edition": "4th",
            "condition": Listing.Condition.GOOD,
            "price": Decimal("250.00"),
        }
        values.update(overrides)
        return Listing.objects.create(**values)

    def listing_data(self, **overrides):
        values = {
            "course": self.course.pk,
            "title": "Database Systems",
            "edition": "4th",
            "condition": Listing.Condition.GOOD,
            "price": "250.00",
            "photo_url": "",
        }
        values.update(overrides)
        return values

    def test_student_can_create_and_browse_a_listing(self):
        self.client.force_login(self.seller)
        form_response = self.client.get(reverse("marketplace:listing_create"))
        self.assertContains(form_response, "Price (PHP)")
        response = self.client.post(
            reverse("marketplace:listing_create"),
            self.listing_data(),
        )

        listing = Listing.objects.get(title="Database Systems")
        self.assertRedirects(response, reverse("marketplace:listing_detail", args=[listing.pk]))
        self.assertEqual(listing.seller, self.seller)
        self.assertEqual(listing.status, Listing.Status.AVAILABLE)
        self.assertContains(self.client.get(reverse("marketplace:listing_catalog")), listing.title)
        self.assertContains(self.client.get(reverse("marketplace:my_listings")), listing.title)

    def test_placeholder_courses_are_available_as_listing_options(self):
        expected_courses = {
            "CSIT321": "Applications Development and Emerging Technologies",
            "CSIT340": "Industry Elective 1",
            "IT365": "Data Analytics 1",
            "CSIT212": "Quantitative Methods",
            "CSIT284": "Platform-based Development 3 (Mobile)",
            "CSIT227": "Object-oriented Programming1",
            "CSIT228": "Object-oriented Programming 2",
            "CSIT111": "Introduction to Computing",
        }
        actual_courses = dict(
            Course.objects.filter(course_code__in=expected_courses).values_list("course_code", "course_name")
        )
        self.assertEqual(actual_courses, expected_courses)

        self.client.force_login(self.seller)
        response = self.client.get(reverse("marketplace:listing_create"))
        for course_name in expected_courses.values():
            self.assertContains(response, course_name)

    def test_listing_form_rejects_nonpositive_price_and_missing_required_details(self):
        self.client.force_login(self.seller)

        for data in (
            self.listing_data(price="0"),
            self.listing_data(edition=""),
            self.listing_data(condition=""),
            self.listing_data(title="   "),
        ):
            response = self.client.post(reverse("marketplace:listing_create"), data)
            self.assertEqual(response.status_code, 200)

        self.assertEqual(Listing.objects.count(), 0)

    def test_seller_can_edit_delete_and_change_status_of_own_listing(self):
        listing = self.create_listing()
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse("marketplace:listing_update", args=[listing.pk]),
            self.listing_data(title="Revised Database Systems", price="225.00"),
        )
        self.assertRedirects(response, reverse("marketplace:listing_detail", args=[listing.pk]))
        listing.refresh_from_db()
        self.assertEqual(listing.title, "Revised Database Systems")
        self.assertEqual(listing.price, Decimal("225.00"))

        response = self.client.post(
            reverse("marketplace:listing_update_status", args=[listing.pk]),
            {"status": Listing.Status.RESERVED},
        )
        self.assertRedirects(response, reverse("marketplace:listing_detail", args=[listing.pk]))
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.RESERVED)

        response = self.client.post(
            reverse("marketplace:listing_update_status", args=[listing.pk]),
            {"status": Listing.Status.SOLD},
        )
        self.assertRedirects(response, reverse("marketplace:listing_detail", args=[listing.pk]))
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.SOLD)

        self.client.post(
            reverse("marketplace:listing_update_status", args=[listing.pk]),
            {"status": Listing.Status.AVAILABLE},
            follow=True,
        )
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.SOLD)

        response = self.client.get(reverse("marketplace:listing_delete", args=[listing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())
        response = self.client.post(reverse("marketplace:listing_delete", args=[listing.pk]))
        self.assertRedirects(response, reverse("marketplace:my_listings"))
        self.assertFalse(Listing.objects.filter(pk=listing.pk).exists())

    def test_students_cannot_modify_another_sellers_listing(self):
        listing = self.create_listing()
        self.client.force_login(self.other_student)

        for route_name in ("listing_update", "listing_delete", "listing_update_status"):
            response = self.client.post(
                reverse(f"marketplace:{route_name}", args=[listing.pk]),
                self.listing_data(),
            )
            self.assertEqual(response.status_code, 404)

        self.assertContains(
            self.client.get(reverse("marketplace:listing_detail", args=[listing.pk])),
            listing.title,
        )

    def test_catalog_filters_by_course_subject_edition_and_price(self):
        matching = self.create_listing()
        self.create_listing(
            title="Calculus",
            course=self.other_course,
            edition="2nd",
            price=Decimal("100.00"),
        )
        self.client.force_login(self.other_student)

        response = self.client.get(
            reverse("marketplace:listing_catalog"),
            {
                "course": self.course.pk,
                "subject": "information",
                "edition": "4",
                "min_price": "200",
                "max_price": "300",
            },
        )

        self.assertContains(response, matching.title)
        self.assertNotContains(response, "Calculus")

    def test_course_code_format_and_twenty_active_listing_limit(self):
        with self.assertRaises(ValidationError):
            Course(course_code="csit327", course_name="Invalid code").full_clean()

        for index in range(20):
            self.create_listing(title=f"Book {index}")

        self.client.force_login(self.seller)
        response = self.client.post(
            reverse("marketplace:listing_create"),
            self.listing_data(title="Twenty-first book"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "at most 20")
        self.assertEqual(Listing.objects.count(), 20)

    def test_admin_can_remove_listing_but_students_cannot_open_moderation(self):
        listing = self.create_listing(status=Listing.Status.SOLD)
        self.client.force_login(self.other_student)
        self.assertEqual(self.client.get(reverse("marketplace:listing_moderation")).status_code, 403)
        self.assertEqual(self.client.get(reverse("marketplace:admin_panel")).status_code, 403)

        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/admin/"), "Admin panel")
        self.assertContains(self.client.get(reverse("marketplace:listing_moderation")), listing.title)
        response = self.client.post(reverse("marketplace:listing_remove", args=[listing.pk]))
        self.assertRedirects(response, reverse("marketplace:listing_moderation"))
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.REMOVED)

    def test_custom_admin_can_manage_courses_and_cannot_delete_courses_with_listings(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("marketplace:course_create"),
            {
                "course_code": "csit399",
                "course_name": "Temporary Course",
                "subject": "Testing",
            },
        )
        self.assertRedirects(response, reverse("marketplace:course_list"))
        course = Course.objects.get(course_code="CSIT399")

        response = self.client.post(
            reverse("marketplace:course_update", args=[course.pk]),
            {
                "course_code": "CSIT399",
                "course_name": "Updated Temporary Course",
                "subject": "Testing",
            },
        )
        self.assertRedirects(response, reverse("marketplace:course_list"))
        course.refresh_from_db()
        self.assertEqual(course.course_name, "Updated Temporary Course")

        self.create_listing(course=course)
        response = self.client.post(reverse("marketplace:course_delete", args=[course.pk]), follow=True)
        self.assertContains(response, "cannot be deleted while textbook listings use it")
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())

        empty_course = Course.objects.create(course_code="CSIT398", course_name="Unused Course")
        response = self.client.post(reverse("marketplace:course_delete", args=[empty_course.pk]))
        self.assertRedirects(response, reverse("marketplace:course_list"))
        self.assertFalse(Course.objects.filter(pk=empty_course.pk).exists())

    def test_anonymous_users_are_sent_to_login(self):
        response = self.client.get(reverse("marketplace:listing_catalog"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('marketplace:listing_catalog')}",
        )

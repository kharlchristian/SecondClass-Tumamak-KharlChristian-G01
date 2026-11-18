from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


course_code_validator = RegexValidator(
    regex=r"^[A-Z]{2,6}[0-9]{2,4}$",
    message="Use 2-6 uppercase letters followed by 2-4 digits, such as CSIT327.",
)


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True, validators=[course_code_validator])
    course_name = models.CharField(max_length=150)
    subject = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["course_code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(course_code__regex=r"^[A-Z]{2,6}[0-9]{2,4}$"),
                name="course_code_format_valid",
            ),
        ]

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Listing(models.Model):
    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        LIKE_NEW = "LIKE_NEW", "Like new"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        POOR = "POOR", "Poor"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        SOLD = "SOLD", "Sold"
        REMOVED = "REMOVED", "Removed"

    ACTIVE_STATUSES = (Status.AVAILABLE, Status.RESERVED)

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="textbook_listings",
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=150)
    edition = models.CharField(max_length=50)
    condition = models.CharField(max_length=20, choices=Condition.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price (PHP)")
    photo_url = models.URLField(max_length=255, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name="listing_price_positive"),
            models.CheckConstraint(condition=Q(title__regex=r"\S"), name="listing_title_not_empty"),
            models.CheckConstraint(
                condition=Q(condition__in=["NEW", "LIKE_NEW", "GOOD", "FAIR", "POOR"]),
                name="listing_condition_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["AVAILABLE", "RESERVED", "SOLD", "REMOVED"]),
                name="listing_status_valid",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.title and not self.title.strip():
            errors["title"] = "The title cannot contain only spaces."

        if self.seller_id and self.status in self.ACTIVE_STATUSES:
            active_listings = self.seller.textbook_listings.filter(status__in=self.ACTIVE_STATUSES)
            if self.pk:
                active_listings = active_listings.exclude(pk=self.pk)
            if active_listings.count() >= 20:
                errors["__all__"] = "You can have at most 20 available or reserved listings."

        if self.pk:
            previous_status = type(self).objects.only("status").get(pk=self.pk).status
            if previous_status in {self.Status.SOLD, self.Status.REMOVED} and self.status in self.ACTIVE_STATUSES:
                errors["status"] = "Sold or removed listings cannot return to an active status."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.title} ({self.course.course_code})"

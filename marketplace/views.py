from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CourseForm, ListingFilterForm, ListingForm, ListingStatusForm
from .models import Course, Listing


User = get_user_model()


def student_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.STUDENT:
            messages.error(request, "The marketplace is available to student accounts.")
            return redirect("accounts:admin_dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


@student_required
def listing_catalog(request):
    form = ListingFilterForm(request.GET or None)
    listings = Listing.objects.filter(status=Listing.Status.AVAILABLE).select_related("course", "seller")
    if form.is_valid():
        filters = form.cleaned_data
        if filters["course"]:
            listings = listings.filter(course=filters["course"])
        if filters["subject"]:
            listings = listings.filter(course__subject__icontains=filters["subject"].strip())
        if filters["edition"]:
            listings = listings.filter(edition__icontains=filters["edition"].strip())
        if filters["condition"]:
            listings = listings.filter(condition=filters["condition"])
        if filters["min_price"] is not None:
            listings = listings.filter(price__gte=filters["min_price"])
        if filters["max_price"] is not None:
            listings = listings.filter(price__lte=filters["max_price"])
    return render(request, "marketplace/listing_catalog.html", {"form": form, "listings": listings})


@student_required
def my_listings(request):
    listings = Listing.objects.filter(seller=request.user).select_related("course")
    return render(request, "marketplace/my_listings.html", {"listings": listings})


@student_required
def listing_create(request):
    form = ListingForm(request.POST or None, seller=request.user)
    if request.method == "POST" and form.is_valid():
        listing = form.save()
        messages.success(request, "Your textbook listing has been created.")
        return redirect("marketplace:listing_detail", pk=listing.pk)
    return render(request, "marketplace/listing_form.html", {"form": form, "is_create": True})


@student_required
def listing_detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related("course", "seller"), pk=pk)
    if listing.seller_id != request.user.id and listing.status != Listing.Status.AVAILABLE:
        raise PermissionDenied
    return render(
        request,
        "marketplace/listing_detail.html",
        {
            "listing": listing,
            "is_owner": listing.seller_id == request.user.id,
            "status_form": ListingStatusForm(listing=listing),
        },
    )


@student_required
def listing_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    form = ListingForm(request.POST or None, instance=listing, seller=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your textbook listing has been updated.")
        return redirect("marketplace:listing_detail", pk=listing.pk)
    return render(request, "marketplace/listing_form.html", {"form": form, "is_create": False, "listing": listing})


@student_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == "POST":
        listing.delete()
        messages.success(request, "Your textbook listing has been deleted.")
        return redirect("marketplace:my_listings")
    return render(request, "marketplace/listing_confirm_delete.html", {"listing": listing})


@student_required
@require_POST
def listing_update_status(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    form = ListingStatusForm(request.POST, listing=listing)
    if form.is_valid():
        listing.status = form.cleaned_data["status"]
        listing.full_clean()
        listing.save()
        messages.success(request, "The listing status has been updated.")
    else:
        for error in form.errors.get("status", form.non_field_errors()):
            messages.error(request, error)
    return redirect("marketplace:listing_detail", pk=listing.pk)


@admin_required
def admin_panel(request):
    context = {
        "total_users": User.objects.count(),
        "student_count": User.objects.filter(role=User.Role.STUDENT).count(),
        "course_count": Course.objects.count(),
        "listing_count": Listing.objects.count(),
        "active_listing_count": Listing.objects.filter(status__in=Listing.ACTIVE_STATUSES).count(),
    }
    return render(request, "marketplace/admin_panel.html", context)


@admin_required
def course_list(request):
    courses = Course.objects.annotate(listing_count=Count("listings"))
    return render(request, "marketplace/course_list.html", {"courses": courses})


@admin_required
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save()
        messages.success(request, f"{course.course_code} has been added.")
        return redirect("marketplace:course_list")
    return render(request, "marketplace/course_form.html", {"form": form, "is_create": True})


@admin_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{course.course_code} has been updated.")
        return redirect("marketplace:course_list")
    return render(
        request,
        "marketplace/course_form.html",
        {"form": form, "is_create": False, "course": course},
    )


@admin_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        try:
            course.delete()
        except ProtectedError:
            messages.error(request, "This course cannot be deleted while textbook listings use it.")
        else:
            messages.success(request, f"{course.course_code} has been deleted.")
        return redirect("marketplace:course_list")
    return render(
        request,
        "marketplace/course_confirm_delete.html",
        {"course": course, "has_listings": course.listings.exists()},
    )


@admin_required
def listing_moderation(request):
    listings = Listing.objects.select_related("course", "seller")
    return render(request, "marketplace/listing_moderation.html", {"listings": listings})


@admin_required
@require_POST
def listing_remove(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.status != Listing.Status.REMOVED:
        listing.status = Listing.Status.REMOVED
        listing.full_clean()
        listing.save()
        messages.success(request, "The listing has been removed from the marketplace.")
    return redirect("marketplace:listing_moderation")

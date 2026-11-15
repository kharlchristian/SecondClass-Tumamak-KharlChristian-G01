from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from .forms import EmailAuthenticationForm, RegistrationForm, UserProfileForm


User = get_user_model()


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        dashboard_name = (
            "accounts:admin_dashboard"
            if self.request.user.role == User.Role.ADMIN
            else "accounts:student_dashboard"
        )
        return reverse(dashboard_name)


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your account has been created. You can now sign in.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.role == User.Role.ADMIN:
        return redirect("accounts:admin_dashboard")
    return redirect("accounts:student_dashboard")


@login_required
def student_dashboard(request):
    if request.user.role != User.Role.STUDENT:
        messages.error(request, "You do not have permission to view the student dashboard.")
        return redirect("accounts:admin_dashboard")
    return render(request, "accounts/student_dashboard.html")


@login_required
def admin_dashboard(request):
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "You do not have permission to view the admin dashboard.")
        return redirect("accounts:student_dashboard")
    context = {
        "total_users": User.objects.count(),
        "student_count": User.objects.filter(role=User.Role.STUDENT).count(),
    }
    return render(request, "accounts/admin_dashboard.html", context)


@login_required
def profile(request):
    form = UserProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})

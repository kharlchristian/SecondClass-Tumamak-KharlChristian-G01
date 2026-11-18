from django import forms
from django.core.exceptions import ValidationError

from .models import Course, Listing


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("course_code", "course_name", "subject")

    def clean_course_code(self):
        return self.cleaned_data["course_code"].strip().upper()


class ListingForm(forms.ModelForm):
    def __init__(self, *args, seller, **kwargs):
        self.seller = seller
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.instance.seller = seller
        self.fields["course"].queryset = Course.objects.all()

    class Meta:
        model = Listing
        fields = ("course", "title", "edition", "condition", "price", "photo_url")
        widgets = {
            "title": forms.TextInput(attrs={"autocomplete": "off"}),
            "edition": forms.TextInput(attrs={"autocomplete": "off"}),
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "photo_url": forms.URLInput(attrs={"autocomplete": "url"}),
        }

    def save(self, commit=True):
        listing = super().save(commit=False)
        listing.seller = self.seller
        if commit:
            listing.full_clean()
            listing.save()
        return listing


class ListingStatusForm(forms.Form):
    status = forms.ChoiceField(choices=(
        (Listing.Status.AVAILABLE, Listing.Status.AVAILABLE.label),
        (Listing.Status.RESERVED, Listing.Status.RESERVED.label),
        (Listing.Status.SOLD, Listing.Status.SOLD.label),
    ))

    def __init__(self, *args, listing, **kwargs):
        self.listing = listing
        super().__init__(*args, **kwargs)
        self.initial.setdefault("status", listing.status)

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        allowed_transitions = {
            Listing.Status.AVAILABLE: {
                Listing.Status.AVAILABLE,
                Listing.Status.RESERVED,
                Listing.Status.SOLD,
            },
            Listing.Status.RESERVED: {
                Listing.Status.AVAILABLE,
                Listing.Status.RESERVED,
                Listing.Status.SOLD,
            },
            Listing.Status.SOLD: {Listing.Status.SOLD},
            Listing.Status.REMOVED: {Listing.Status.REMOVED},
        }
        if new_status not in allowed_transitions[self.listing.status]:
            raise ValidationError("Sold or removed listings cannot return to an active status.")
        return new_status


class ListingFilterForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False)
    subject = forms.CharField(max_length=100, required=False)
    edition = forms.CharField(max_length=50, required=False)
    condition = forms.ChoiceField(
        choices=(("", "Any condition"),) + tuple(Listing.Condition.choices),
        required=False,
    )
    min_price = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2, required=False)
    max_price = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2, required=False)

    def clean(self):
        cleaned_data = super().clean()
        minimum = cleaned_data.get("min_price")
        maximum = cleaned_data.get("max_price")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError("Minimum price cannot be greater than maximum price.")
        return cleaned_data

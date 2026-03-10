from django import forms

from .models import Booking, Expense, OwnerProfile, Vehicle


class OwnerProfileForm(forms.ModelForm):
    class Meta:
        model = OwnerProfile
        fields = [
            "business_name",
            "phone_number",
            "address",
            "license_number",
            "profile_photo",
            "profile_photo_url",
        ]


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "category",
            "name",
            "brand",
            "model_year",
            "registration_number",
            "photo",
            "photo_url",
            "fuel_type",
            "seats",
            "transmission",
            "rent_per_day",
            "is_available",
            "notes",
        ]
        labels = {
            "photo": "Primary image upload",
            "photo_url": "Primary image URL",
        }
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "photo_url": forms.URLInput(attrs={"placeholder": "Optional image URL"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "customer_name",
            "customer_phone",
            "vehicle",
            "start_date",
            "end_date",
            "total_price",
            "advance_paid",
            "status",
            "picked_up_at",
            "returned_at",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "picked_up_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "returned_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "amount", "spent_on", "notes"]
        widgets = {
            "spent_on": forms.DateInput(attrs={"type": "date"}),
        }

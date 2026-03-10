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
            "fuel_type",
            "seats",
            "transmission",
            "rent_per_day",
            "is_available",
            "photo",
            "photo_url",
            "notes",
        ]


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

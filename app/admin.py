from django.contrib import admin

from .models import Booking, CustomerProfile, Expense, Feedback, OwnerProfile, Vehicle, VehicleImage


@admin.action(description="Verify selected partners and activate users")
def verify_partners(modeladmin, request, queryset):
    queryset.update(is_verified=True)
    for profile in queryset.select_related("user"):
        if not profile.user.is_active:
            profile.user.is_active = True
            profile.user.save(update_fields=["is_active"])


@admin.action(description="Unverify selected partners")
def unverify_partners(modeladmin, request, queryset):
    queryset.update(is_verified=False)


@admin.action(description="Verify selected vehicles")
def verify_vehicles(modeladmin, request, queryset):
    queryset.update(is_verified=True)


@admin.action(description="Unverify selected vehicles")
def unverify_vehicles(modeladmin, request, queryset):
    queryset.update(is_verified=False)


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "user",
        "phone_number",
        "is_verified",
        "total_revenue",
        "total_profit",
    )
    list_filter = ("is_verified",)
    search_fields = ("business_name", "user__username", "phone_number", "license_number")
    actions = (verify_partners, unverify_partners)


class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "owner",
        "registration_number",
        "rent_per_day",
        "is_available",
        "is_verified",
    )
    list_filter = ("category", "fuel_type", "is_available", "is_verified", "owner")
    search_fields = ("name", "brand", "registration_number", "owner__business_name")
    actions = (verify_vehicles, unverify_vehicles)
    inlines = [VehicleImageInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "vehicle",
        "owner",
        "start_date",
        "end_date",
        "total_price",
        "status",
    )
    list_filter = ("status", "start_date", "end_date", "owner", "vehicle__category")
    search_fields = ("customer_name", "customer_phone", "vehicle__registration_number")
    autocomplete_fields = ("owner", "vehicle")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "amount", "spent_on")
    list_filter = ("spent_on", "owner")
    search_fields = ("title", "owner__business_name")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("email", "name", "message")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "lpu_id", "created_at")
    search_fields = ("email", "name", "phone", "lpu_id")

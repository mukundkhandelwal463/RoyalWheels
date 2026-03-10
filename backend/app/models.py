from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OwnerProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_profile",
    )
    business_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    profile_photo_url = models.URLField(blank=True)
    profile_photo = models.FileField(upload_to="profile_photos/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["business_name"]

    def __str__(self):
        return f"{self.business_name} ({self.user.username})"

    @property
    def total_revenue(self):
        total = self.bookings.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED]
        ).aggregate(total=Sum("total_price"))["total"]
        return total or Decimal("0.00")

    @property
    def total_expenses(self):
        expenses = self.expenses.aggregate(total=Sum("amount"))["total"]
        return expenses or Decimal("0.00")

    @property
    def total_profit(self):
        return self.total_revenue - self.total_expenses


class Vehicle(TimestampedModel):
    class Category(models.TextChoices):
        CAR = "car", "Car"
        BIKE = "bike", "Bike"

    class FuelType(models.TextChoices):
        PETROL = "petrol", "Petrol"
        DIESEL = "diesel", "Diesel"
        ELECTRIC = "electric", "Electric"
        CNG = "cng", "CNG"
        HYBRID = "hybrid", "Hybrid"

    owner = models.ForeignKey(
        OwnerProfile,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    category = models.CharField(max_length=10, choices=Category.choices)
    name = models.CharField(max_length=120)
    brand = models.CharField(max_length=80)
    model_year = models.PositiveIntegerField()
    registration_number = models.CharField(max_length=25, unique=True)
    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        default=FuelType.PETROL,
    )
    seats = models.PositiveSmallIntegerField(default=2)
    transmission = models.CharField(max_length=20, blank=True)
    rent_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    photo_url = models.URLField(blank=True)
    photo = models.FileField(upload_to="vehicle_photos/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "brand", "name"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.brand} {self.name}"


class VehicleImage(TimestampedModel):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.FileField(upload_to="vehicle_gallery/")
    caption = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.vehicle} image"


class Booking(TimestampedModel):
    class RentalUnit(models.TextChoices):
        DAY = "day", "Per Day"
        HOUR = "hour", "Per Hour"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        COD = "cod", "Cash on Delivery"

    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    customer_address = models.TextField(blank=True)
    customer_lpu_id = models.CharField(max_length=60, blank=True)
    customer_license_number = models.CharField(max_length=60, blank=True)
    customer_age = models.PositiveSmallIntegerField(blank=True, null=True)
    driving_license_doc = models.FileField(upload_to="booking_docs/licenses/", blank=True, null=True)
    student_id_doc = models.FileField(upload_to="booking_docs/student_ids/", blank=True, null=True)
    owner = models.ForeignKey(
        OwnerProfile,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    rental_unit = models.CharField(
        max_length=10,
        choices=RentalUnit.choices,
        default=RentalUnit.DAY,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    advance_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    payment_method = models.CharField(max_length=20, blank=True)
    razorpay_order_id = models.CharField(max_length=40, blank=True)
    razorpay_payment_id = models.CharField(max_length=40, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    picked_up_at = models.DateTimeField(blank=True, null=True)
    returned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return f"{self.customer_name} - {self.vehicle} ({self.status})"

    @property
    def remaining_amount(self):
        return self.total_price - self.advance_paid

    @property
    def duration_days(self):
        days = (self.end_date - self.start_date).days + 1
        return max(days, 1)

    @property
    def duration_hours(self):
        if not self.start_time or not self.end_time:
            return None
        start = timezone.datetime.combine(self.start_date, self.start_time)
        end = timezone.datetime.combine(self.end_date, self.end_time)
        if end <= start:
            return None
        seconds = (end - start).total_seconds()
        return max(int((seconds + 3599) // 3600), 1)

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.returned_at = timezone.now()
        self.save(update_fields=["status", "returned_at", "updated_at"])


class Expense(TimestampedModel):
    owner = models.ForeignKey(
        OwnerProfile,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_on = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-spent_on", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Feedback(TimestampedModel):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(blank=True, null=True)
    message = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email or 'Anonymous'} ({self.created_at:%Y-%m-%d})"


class CustomerProfile(TimestampedModel):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    address = models.TextField(blank=True)
    lpu_id = models.CharField(max_length=60, blank=True, null=True, unique=True)
    license_number = models.CharField(max_length=60, blank=True)
    driving_license_doc = models.FileField(
        upload_to="customer_docs/licenses/",
        blank=True,
        null=True,
    )
    student_id_doc = models.FileField(
        upload_to="customer_docs/student_ids/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

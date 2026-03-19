import base64
import hashlib
import hmac
import json
import logging
import math
import random
import smtplib
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import cloudinary.uploader
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db import connection
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.db.utils import OperationalError
from django.templatetags.static import static
from django.http import FileResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings

from .forms import ExpenseForm, OwnerProfileForm, VehicleForm
from .models import Booking, CustomerProfile, Expense, Feedback, OwnerProfile, Vehicle, VehicleImage

logger = logging.getLogger(__name__)


def _partners_queryset():
    return (
        OwnerProfile.objects.annotate(
            total_vehicles=Count("vehicles"),
            cars_count=Count(
                "vehicles",
                filter=Q(vehicles__category=Vehicle.Category.CAR),
            ),
            bikes_count=Count(
                "vehicles",
                filter=Q(vehicles__category=Vehicle.Category.BIKE),
            ),
        )
        .filter(total_vehicles__gt=0, is_verified=True, user__is_active=True)
        .select_related("user")
        .order_by("-total_vehicles", "business_name")
    )


def _vehicle_image_url(vehicle):
    if vehicle.photo and getattr(vehicle.photo, "name", ""):
        try:
            if vehicle.photo.storage.exists(vehicle.photo.name):
                return vehicle.photo.url
        except Exception:
            pass

    latest_gallery_image = vehicle.images.order_by("-created_at", "-id").first()
    if latest_gallery_image and getattr(latest_gallery_image.image, "name", ""):
        try:
            if latest_gallery_image.image.storage.exists(latest_gallery_image.image.name):
                return latest_gallery_image.image.url
        except Exception:
            pass

    if vehicle.photo_url:
        candidate = str(vehicle.photo_url).strip()
        parsed = urllib.parse.urlparse(candidate)
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        if parsed.path and media_url and parsed.path.startswith(media_url):
            relative_media_path = parsed.path[len(media_url):].lstrip("/")
            absolute_media_path = Path(getattr(settings, "MEDIA_ROOT", "")) / relative_media_path
            if absolute_media_path.exists():
                return candidate
        elif candidate:
            return candidate

    return _vehicle_fallback_image_url(vehicle)


def _owner_profile_image_url(owner):
    if not owner:
        return ""

    if owner.profile_photo and getattr(owner.profile_photo, "name", ""):
        try:
            if owner.profile_photo.storage.exists(owner.profile_photo.name):
                return owner.profile_photo.url
        except Exception:
            pass

    if owner.profile_photo_url:
        candidate = str(owner.profile_photo_url).strip()
        parsed = urllib.parse.urlparse(candidate)
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        if parsed.path and media_url and parsed.path.startswith(media_url):
            relative_media_path = parsed.path[len(media_url):].lstrip("/")
            absolute_media_path = Path(getattr(settings, "MEDIA_ROOT", "")) / relative_media_path
            if absolute_media_path.exists():
                return candidate
        elif candidate:
            return candidate

    return static("assets/logo.jpg")


def _prepare_owner_profile(owner):
    if not owner:
        return owner

    if owner.profile_photo and getattr(owner.profile_photo, "name", ""):
        try:
            photo_exists = owner.profile_photo.storage.exists(owner.profile_photo.name)
        except Exception:
            photo_exists = False
        if not photo_exists and owner.profile_photo_url:
            owner.profile_photo = None
            owner.save(update_fields=["profile_photo", "updated_at"])

    owner.display_profile_photo_url = _owner_profile_image_url(owner)
    return owner


def _vehicle_fallback_image_url(vehicle):
    label = f"{vehicle.brand} {vehicle.name}".lower()

    if any(token in label for token in ["bmw", "x7", "x5"]):
        return static("assets/BMW.png")
    if any(token in label for token in ["hunter", "enfield", "classic", "duke", "r15", "apache", "pulsar"]):
        return static("assets/hunter.png")
    if any(token in label for token in ["creta", "city", "verna", "baleno", "harrier", "xuv"]):
        return static("assets/hunter2.png")
    return static("assets/logo.jpg")


def _existing_file_response(field_file, *, filename=None):
    if not field_file or not getattr(field_file, "name", ""):
        return None
    try:
        if not field_file.storage.exists(field_file.name):
            return None
        handle = field_file.open("rb")
    except Exception:
        return None
    return FileResponse(handle, as_attachment=True, filename=filename or field_file.name.rsplit("/", 1)[-1])


def _find_customer_profile_for_booking(booking):
    lookup_lpu = (booking.customer_lpu_id or "").strip()
    lookup_email = (booking.customer_email or "").strip()
    profile = None
    if lookup_lpu:
        profile = CustomerProfile.objects.filter(lpu_id__iexact=lookup_lpu).first()
    if profile is None and lookup_email:
        profile = CustomerProfile.objects.filter(email__iexact=lookup_email).first()
    return profile


def _clone_uploaded_file(uploaded_file):
    if not uploaded_file:
        return None
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    content = uploaded_file.read()
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    return ContentFile(content, name=getattr(uploaded_file, "name", "upload.bin"))


def _upload_image_to_cloudinary(uploaded_file, folder):
    if not uploaded_file or not getattr(settings, "CLOUDINARY_ENABLED", False):
        return None
    try:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        result = cloudinary.uploader.upload(
            uploaded_file,
            folder=folder,
            resource_type="image",
            overwrite=False,
            use_filename=True,
            unique_filename=True,
        )
        return str(result.get("secure_url") or "").strip() or None
    except Exception as exc:
        logger.warning("Cloudinary upload failed for %s: %s", getattr(uploaded_file, "name", "upload"), exc)
        return None
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def _upload_data_url_to_cloudinary(data_url, folder, prefix):
    if not data_url or not getattr(settings, "CLOUDINARY_ENABLED", False):
        return None
    try:
        result = cloudinary.uploader.upload(
            data_url,
            folder=folder,
            resource_type="auto",
            public_id=f"{prefix}_{uuid.uuid4().hex[:12]}",
            overwrite=False,
            unique_filename=False,
        )
        return str(result.get("secure_url") or "").strip() or None
    except Exception as exc:
        logger.warning("Cloudinary data-url upload failed for %s: %s", prefix, exc)
        return None


def _document_url(field_file, url_value):
    if url_value:
        return str(url_value).strip()
    if field_file and getattr(field_file, "name", ""):
        try:
            if field_file.storage.exists(field_file.name):
                return field_file.url
        except Exception:
            return ""
    return ""


def _apply_vehicle_primary_image(vehicle, request_files):
    primary_upload = request_files.get("photo")
    gallery_uploads = list(request_files.getlist("gallery_images"))
    upload_folder = f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/vehicles"

    if primary_upload:
        cloudinary_url = _upload_image_to_cloudinary(primary_upload, upload_folder)
        if cloudinary_url:
            vehicle.photo = None
            vehicle.photo_url = cloudinary_url
        else:
            vehicle.photo = primary_upload
            vehicle.photo_url = ""
        return gallery_uploads

    if gallery_uploads:
        cloudinary_url = _upload_image_to_cloudinary(gallery_uploads[-1], upload_folder)
        if cloudinary_url:
            vehicle.photo = None
            vehicle.photo_url = cloudinary_url
        else:
            cloned_primary = _clone_uploaded_file(gallery_uploads[-1])
            if cloned_primary is not None:
                vehicle.photo = cloned_primary
                vehicle.photo_url = ""
    return gallery_uploads


OTP_EXPIRY_SECONDS = 300


def _otp_session_store(request):
    store = request.session.get("otp_store")
    if not isinstance(store, dict):
        store = {}
    return store


def _otp_verified_map(request):
    verified = request.session.get("otp_verified")
    if not isinstance(verified, dict):
        verified = {}
    return verified


def _otp_verified_key(purpose, channel, target):
    return f"{purpose}:{channel}:{str(target).strip().lower()}"


def _mark_otp_verified(request, purpose, channel, target):
    verified = _otp_verified_map(request)
    verified[_otp_verified_key(purpose, channel, target)] = int(time.time())
    request.session["otp_verified"] = verified
    request.session.modified = True


def _is_otp_verified(request, purpose, channel, target):
    if not target:
        return False
    verified = _otp_verified_map(request)
    ts = verified.get(_otp_verified_key(purpose, channel, target))
    if not ts:
        return False
    return int(time.time()) - int(ts) <= OTP_EXPIRY_SECONDS


def _create_otp(request, purpose, channel, target):
    otp_id = uuid.uuid4().hex
    code = f"{random.randint(0, 999999):06d}"
    store = _otp_session_store(request)
    store[otp_id] = {
        "purpose": str(purpose),
        "channel": str(channel),
        "target": str(target).strip(),
        "code": code,
        "expires_at": int(time.time()) + OTP_EXPIRY_SECONDS,
        "verified": False,
    }
    request.session["otp_store"] = store
    request.session.modified = True
    return otp_id, code


def _normalize_indian_phone(raw_phone):
    digits = "".join(ch for ch in str(raw_phone or "") if ch.isdigit())
    if digits.startswith("91") and len(digits) >= 12:
        local = digits[-10:]
    elif len(digits) >= 10:
        local = digits[-10:]
    else:
        return ""
    return f"+91{local}"


def _send_email_otp(target, code):
    allow_dev_fallback = bool(getattr(settings, "OTP_DEV_FALLBACK", False))

    if "console" in str(getattr(settings, "EMAIL_BACKEND", "")).lower():
        if allow_dev_fallback:
            print(f"[DEV EMAIL OTP] {target}: {code}")
            return True, "OTP sent successfully."
        return False, "Email backend is console. Configure SMTP to deliver OTP to mailbox."

    if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        if allow_dev_fallback:
            print(f"[DEV EMAIL OTP] {target}: {code}")
            return True, "OTP sent successfully."
        return False, "Email service is not configured. Set EMAIL_HOST, EMAIL_HOST_USER and EMAIL_HOST_PASSWORD."

    try:
        send_mail(
            subject="RoyalWheels OTP Verification",
            message=f"Your OTP is {code}. It is valid for 5 minutes.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@royalwheels.local"),
            recipient_list=[target],
            fail_silently=False,
        )
        return True, "OTP sent to email."
    except smtplib.SMTPAuthenticationError as exc:
        logger.exception("Email OTP SMTP authentication failed for target=%s", target)
        message = "Email login failed. Gmail SMTP requires a 16-character App Password in EMAIL_HOST_PASSWORD."
        if allow_dev_fallback:
            print(f"[DEV EMAIL OTP FALLBACK] {target}: {code} (email auth failed: {exc})")
            return True, message
        return False, message
    except Exception as exc:
        logger.exception("Email OTP delivery failed for target=%s", target)
        if allow_dev_fallback:
            print(f"[DEV EMAIL OTP FALLBACK] {target}: {code} (email send failed: {exc})")
            return True, "OTP generated successfully."
        return False, "Email delivery failed. Please try again later."


def _send_phone_otp(target, code):
    allow_dev_fallback = bool(getattr(settings, "OTP_DEV_FALLBACK", False))

    if not settings.FAST2SMS_API_KEY:
        if allow_dev_fallback:
            print(f"[DEV SMS OTP] {target}: {code}")
            return True, "OTP sent successfully."
        return False, "SMS OTP service not configured."

    api_url = "https://www.fast2sms.com/dev/bulkV2"

    phone_number = target.replace("+91", "").strip()

    payload = urllib.parse.urlencode({
        "route": "q",   # ✅ IMPORTANT CHANGE
        "message": f"Your RoyalWheels OTP is {code}. Valid for 5 minutes.",
        "language": "english",
        "numbers": phone_number,
    }).encode("utf-8")

    request_obj = urllib.request.Request(api_url, data=payload, method="POST")
    request_obj.add_header("authorization", settings.FAST2SMS_API_KEY)
    request_obj.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request_obj, timeout=15) as response:
            response_data = json.loads(response.read().decode())

            if not response_data.get("return"):
                return False, response_data.get("message", "SMS provider rejected OTP request.")

    except Exception as exc:
        if allow_dev_fallback:
            print(f"[DEV SMS OTP FALLBACK] {target}: {code} (sms send failed: {exc})")
            return True, "OTP generated successfully."
        if isinstance(exc, urllib.error.HTTPError) or isinstance(exc, urllib.error.URLError):
            return False, f"SMS delivery failed: {getattr(exc, 'reason', 'unknown error')}"
        return False, "SMS delivery failed. Please try again later."

    return True, "OTP sent to phone."


def _razorpay_basic_auth_header():
    key_id = (getattr(settings, "RAZORPAY_KEY_ID", "") or "").strip()
    key_secret = (getattr(settings, "RAZORPAY_KEY_SECRET", "") or "").strip()
    if not key_id or not key_secret:
        raise ValueError(
            "Razorpay keys are not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in your environment and restart the server."
        )
    token = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _razorpay_create_order(*, amount_paise, receipt, currency, notes=None):
    api_url = "https://api.razorpay.com/v1/orders"
    payload = {
        "amount": int(amount_paise),
        "currency": currency,
        "receipt": str(receipt),
        "payment_capture": 1,
    }
    if notes:
        payload["notes"] = notes

    request_obj = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request_obj.add_header("Authorization", _razorpay_basic_auth_header())
    request_obj.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request_obj, timeout=20) as response:
        response_data = response.read().decode("utf-8") or "{}"
        return json.loads(response_data)


def _razorpay_expected_signature(*, order_id, payment_id):
    secret = (getattr(settings, "RAZORPAY_KEY_SECRET", "") or "").encode("utf-8")
    message = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def home(request):
    partners_qs = _partners_queryset().order_by("-created_at", "-total_vehicles", "business_name")
    return render(
        request,
        "Home_index.html",
        {
            "total_vehicles": Vehicle.objects.filter(owner__is_verified=True, owner__user__is_active=True).count(),
            "total_partners": partners_qs.count(),
            "partners": partners_qs[:6],
        },
    )


def cars_page(request):
    cars = Vehicle.objects.select_related("owner").prefetch_related("images").filter(
        category=Vehicle.Category.CAR,
        owner__is_verified=True,
        owner__user__is_active=True,
    )
    for vehicle in cars:
        vehicle.display_image_url = _vehicle_image_url(vehicle)
        vehicle.gallery_urls = [img.image.url for img in vehicle.images.all()[:4]]
    return render(request, "Car.html", {"vehicles": cars})


def bikes_page(request):
    bikes = Vehicle.objects.select_related("owner").prefetch_related("images").filter(
        category=Vehicle.Category.BIKE,
        owner__is_verified=True,
        owner__user__is_active=True,
    )
    for vehicle in bikes:
        vehicle.display_image_url = _vehicle_image_url(vehicle)
        vehicle.gallery_urls = [img.image.url for img in vehicle.images.all()[:4]]
    return render(request, "Bikes.html", {"vehicles": bikes})


def partners_page(request):
    return render(request, "AllPartners.html", {"partners": _partners_queryset()})


@require_GET
def search_page(request):
    query = str(request.GET.get("q", "")).strip()

    vehicles_qs = Vehicle.objects.select_related("owner").prefetch_related("images").filter(
        owner__is_verified=True,
        owner__user__is_active=True,
    )

    partners_qs = _partners_queryset()

    if query:
        vehicles_qs = vehicles_qs.filter(
            Q(brand__icontains=query)
            | Q(name__icontains=query)
            | Q(owner__business_name__icontains=query)
        )
        partners_qs = partners_qs.filter(business_name__icontains=query)
    else:
        vehicles_qs = vehicles_qs.none()
        partners_qs = partners_qs.none()

    cars = list(vehicles_qs.filter(category=Vehicle.Category.CAR)[:12])
    bikes = list(vehicles_qs.filter(category=Vehicle.Category.BIKE)[:12])

    for vehicle in [*cars, *bikes]:
        vehicle.display_image_url = _vehicle_image_url(vehicle)
        vehicle.gallery_urls = [img.image.url for img in vehicle.images.all()[:4]]

    return render(
        request,
        "Search.html",
        {
            "q": query,
            "cars": cars,
            "bikes": bikes,
            "partners": list(partners_qs[:12]),
        },
    )


def my_bookings_page(request):
    return render(request, "MyBooking.html")


def profile_page(request):
    return render(request, "profile.html")


def login_page(request):
    return render(
        request,
        "login.html",
        {
            "google_client_id": (getattr(settings, "GOOGLE_CLIENT_ID", "") or "").strip(),
        },
    )


def user_forgot_password_page(request):
    return render(request, "forgot_password.html")


def signup_page(request):
    return render(request, "signup.html")


def book_now_page(request):
    return render(request, "Book_now.html")


def payment_page(request):
    return render(request, "payment.html")


def admin_login_page(request):
    if request.user.is_authenticated:
        return redirect("owner_dashboard")

    if request.method == "POST":
        username_or_email = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username_or_email, password=password)

        if user is None and "@" in username_or_email:
            existing_user = get_user_model().objects.filter(email__iexact=username_or_email).first()
            if existing_user:
                user = authenticate(request, username=existing_user.username, password=password)

        if user is None:
            messages.error(request, "Invalid username/email or password.")
        else:
            login(request, user)
            return redirect("owner_dashboard")

    return render(request, "admin/admin_login.html")


def admin_forgot_password_page(request):
    if request.user.is_authenticated:
        return redirect("owner_dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        phone = _normalize_indian_phone(request.POST.get("phone"))
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if not email or not phone or not password or not confirm_password:
            messages.error(request, "Please fill all fields.")
            return render(request, "admin/admin_forgot_password.html")

        if password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return render(request, "admin/admin_forgot_password.html")

        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        owner_profile = OwnerProfile.objects.filter(user=user).first() if user else None
        if user is None or owner_profile is None:
            messages.error(request, "No admin account found for this email.")
            return render(request, "admin/admin_forgot_password.html")

        if _normalize_indian_phone(owner_profile.phone_number) != phone:
            messages.error(request, "Provided phone number does not match this admin account.")
            return render(request, "admin/admin_forgot_password.html")

        if not _is_otp_verified(request, "admin_forgot", "email", email):
            messages.error(request, "Please verify email OTP first.")
            return render(request, "admin/admin_forgot_password.html")

        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
            return render(request, "admin/admin_forgot_password.html")

        user.set_password(password)
        user.save(update_fields=["password"])
        messages.success(request, "Password reset successful. Please login.")
        return redirect("admin_login_page")

    return render(request, "admin/admin_forgot_password.html")


def admin_signup_page(request):
    if request.user.is_authenticated:
        return redirect("owner_dashboard")

    if request.method == "POST":
        shop_name = (request.POST.get("shop") or "").strip()
        owner_name = (request.POST.get("owner") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        phone = _normalize_indian_phone(request.POST.get("phone"))
        address = (request.POST.get("address") or "").strip()
        gst = (request.POST.get("gst") or "").strip()
        password = request.POST.get("password") or ""

        if not shop_name or not owner_name or not email or not phone or not password:
            messages.error(request, "Shop name, owner name, email, phone and password are required.")
            return render(request, "admin/admin_signup.html")

        if not _is_otp_verified(request, "admin_signup", "email", email):
            messages.error(request, "Please verify email OTP first.")
            return render(request, "admin/admin_signup.html")

        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, "admin/admin_signup.html")

        base_username = "".join(ch for ch in owner_name.lower().replace(" ", "_") if ch.isalnum() or ch == "_")
        username = base_username or "shopkeeper"
        count = 1
        while user_model.objects.filter(username=username).exists():
            username = f"{base_username or 'shopkeeper'}{count}"
            count += 1

        user = user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=owner_name,
        )
        OwnerProfile.objects.create(
            user=user,
            business_name=shop_name,
            phone_number=phone,
            address=address,
            license_number=gst,
            profile_photo_url=(request.POST.get("photo_url") or "").strip(),
        )
        messages.success(request, "Shopkeeper account created. Please login.")
        return redirect("admin_login_page")

    return render(request, "admin/admin_signup.html")


@login_required
def shopkeeper_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("admin_login_page")


@login_required
def owner_dashboard_api(request):
    owner = get_object_or_404(OwnerProfile, user=request.user)
    data = {
        "owner": owner.business_name,
        "vehicles": owner.vehicles.count(),
        "active_bookings": owner.bookings.filter(status=Booking.Status.CONFIRMED).count(),
        "completed_bookings": owner.bookings.filter(status=Booking.Status.COMPLETED).count(),
        "total_revenue": float(owner.total_revenue),
        "total_expenses": float(owner.total_expenses),
        "total_profit": float(owner.total_profit),
    }
    return JsonResponse(data)


@login_required
def owner_dashboard(request):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    legacy_booking_schema = False
    deferred_legacy_fields = (
        "customer_email",
        "customer_address",
        "customer_lpu_id",
        "customer_license_number",
        "customer_age",
        "driving_license_doc",
        "student_id_doc",
    )
    try:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, Booking._meta.db_table)
            legacy_booking_schema = not any(col.name == "customer_email" for col in description)
    except OperationalError:
        # If introspection fails, keep dashboard resilient by using only legacy-safe columns.
        legacy_booking_schema = True

    booking_base_qs = owner.bookings.select_related("vehicle") if owner else None
    if legacy_booking_schema and booking_base_qs is not None:
        booking_base_qs = booking_base_qs.defer(*deferred_legacy_fields)

    active_rentals = (
        booking_base_qs
        .filter(status=Booking.Status.CONFIRMED)
        .order_by("start_date")[:10]
        if booking_base_qs is not None
        else []
    )
    pending_bookings = (
        booking_base_qs
        .filter(status=Booking.Status.PENDING)
        .order_by("-created_at")[:10]
        if booking_base_qs is not None
        else []
    )
    return render(
        request,
        "management/dashboard.html",
        {
            "owner": owner,
            "vehicles_count": owner.vehicles.count() if owner else 0,
            "active_bookings": (
                owner.bookings.filter(status=Booking.Status.CONFIRMED).count() if owner else 0
            ),
            "completed_bookings": (
                owner.bookings.filter(status=Booking.Status.COMPLETED).count() if owner else 0
            ),
            "total_revenue": owner.total_revenue if owner else Decimal("0.00"),
            "total_expenses": owner.total_expenses if owner else Decimal("0.00"),
            "total_profit": owner.total_profit if owner else Decimal("0.00"),
            "active_rentals_rows": active_rentals,
            "pending_bookings": pending_bookings,
            "legacy_booking_schema": legacy_booking_schema,
        },
    )


@login_required
@require_POST
def booking_decision(request, booking_id):
    owner = get_object_or_404(OwnerProfile, user=request.user)
    booking = get_object_or_404(Booking, id=booking_id, owner=owner)
    decision = (request.POST.get("decision") or "").lower()

    if decision == "accept":
        booking.status = Booking.Status.CONFIRMED
        booking.vehicle.is_available = False
        booking.vehicle.save(update_fields=["is_available", "updated_at"])
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Booking accepted.")
    elif decision == "reject":
        booking.status = Booking.Status.CANCELLED
        booking.vehicle.is_available = True
        booking.vehicle.save(update_fields=["is_available", "updated_at"])
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Booking rejected.")
    elif decision == "complete":
        if booking.status != Booking.Status.CONFIRMED:
            messages.error(request, "Only confirmed bookings can be completed.")
        else:
            booking.vehicle.is_available = True
            booking.vehicle.save(update_fields=["is_available", "updated_at"])
            booking.mark_completed()
            messages.success(request, "Booking marked completed and vehicle is available again.")
    else:
        messages.error(request, "Invalid booking action.")

    referer = request.META.get("HTTP_REFERER", "")
    if "/management/bookings/" in referer:
        return redirect("booking_manage")
    return redirect("owner_dashboard")


@login_required
def owner_profile_manage(request):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    form = OwnerProfileForm(request.POST or None, request.FILES or None, instance=owner)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile_upload = request.FILES.get("profile_photo")
        if profile_upload:
            cloudinary_url = _upload_image_to_cloudinary(
                profile_upload,
                f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/owner_profiles",
            )
            if cloudinary_url:
                profile.profile_photo = None
                profile.profile_photo_url = cloudinary_url
        profile.save()
        messages.success(request, "Profile saved successfully.")
        return redirect("owner_profile_manage")
    owner = _prepare_owner_profile(owner)
    return render(
        request,
        "management/profile_manage.html",
        {"form": form, "owner": owner},
    )


@login_required
def vehicle_manage(request):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")
    form = VehicleForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        vehicle = form.save(commit=False)
        vehicle.owner = owner
        gallery_uploads = _apply_vehicle_primary_image(vehicle, request.FILES)
        vehicle.save()
        for uploaded in gallery_uploads:
            VehicleImage.objects.create(vehicle=vehicle, image=uploaded)
        messages.success(request, "Vehicle added successfully.")
        return redirect("vehicle_manage")

    vehicles = owner.vehicles.prefetch_related("images").all()
    for vehicle in vehicles:
        vehicle.display_image_url = _vehicle_image_url(vehicle)
        vehicle.fallback_image_url = _vehicle_fallback_image_url(vehicle)
    return render(
        request,
        "management/vehicle_manage.html",
        {"form": form, "vehicles": vehicles, "owner": owner},
    )


@login_required
def vehicle_edit(request, vehicle_id):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")

    vehicle = get_object_or_404(Vehicle.objects.prefetch_related("images"), id=vehicle_id, owner=owner)
    form = VehicleForm(request.POST or None, request.FILES or None, instance=vehicle)
    if request.method == "POST" and form.is_valid():
        vehicle = form.save(commit=False)
        gallery_uploads = _apply_vehicle_primary_image(vehicle, request.FILES)
        vehicle.save()
        form.save_m2m()
        for uploaded in gallery_uploads:
            VehicleImage.objects.create(vehicle=vehicle, image=uploaded)
        messages.success(request, "Vehicle updated successfully.")
        return redirect("vehicle_manage")

    vehicle.display_image_url = _vehicle_image_url(vehicle)
    vehicle.fallback_image_url = _vehicle_fallback_image_url(vehicle)

    return render(
        request,
        "management/vehicle_edit.html",
        {"form": form, "vehicle": vehicle, "owner": owner},
    )


@login_required
@require_POST
def vehicle_delete(request, vehicle_id):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")

    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=owner)
    try:
        vehicle.delete()
    except ProtectedError:
        messages.error(
            request,
            "This vehicle cannot be deleted because it is linked to existing bookings. Complete or remove those bookings first.",
        )
    else:
        messages.success(request, "Vehicle deleted.")
    return redirect("vehicle_manage")


@login_required
@require_POST
def vehicle_image_delete(request, image_id):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")

    image = get_object_or_404(VehicleImage.objects.select_related("vehicle"), id=image_id, vehicle__owner=owner)
    vehicle_id = image.vehicle_id
    image.delete()
    messages.success(request, "Vehicle image removed.")
    return redirect("vehicle_edit", vehicle_id=vehicle_id)


@login_required
def booking_manage(request):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")
    bookings = owner.bookings.select_related("vehicle").order_by("-created_at")
    return render(
        request,
        "management/booking_manage.html",
        {"bookings": bookings, "owner": owner},
    )


@login_required
def booking_document_download(request, booking_id, document_type):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")

    booking = get_object_or_404(Booking.objects.select_related("vehicle", "owner"), id=booking_id, owner=owner)

    if document_type == "license":
        if booking.driving_license_doc_url:
            return redirect(booking.driving_license_doc_url)
        response = _existing_file_response(
            booking.driving_license_doc,
            filename=f"{booking.customer_name or 'customer'}-driving-license",
        )
        if response:
            return response
        profile = _find_customer_profile_for_booking(booking)
        if profile and profile.driving_license_doc_url:
            return redirect(profile.driving_license_doc_url)
        response = _existing_file_response(
            profile.driving_license_doc if profile else None,
            filename=f"{booking.customer_name or 'customer'}-driving-license",
        )
        if response:
            return response
    elif document_type == "student-id":
        if booking.student_id_doc_url:
            return redirect(booking.student_id_doc_url)
        response = _existing_file_response(
            booking.student_id_doc,
            filename=f"{booking.customer_name or 'customer'}-college-id",
        )
        if response:
            return response
        profile = _find_customer_profile_for_booking(booking)
        if profile and profile.student_id_doc_url:
            return redirect(profile.student_id_doc_url)
        response = _existing_file_response(
            profile.student_id_doc if profile else None,
            filename=f"{booking.customer_name or 'customer'}-college-id",
        )
        if response:
            return response
    else:
        raise Http404("Unknown document type.")

    raise Http404("Document file not found.")


@login_required
def expense_manage(request):
    owner = _prepare_owner_profile(OwnerProfile.objects.filter(user=request.user).first())
    if not owner:
        messages.error(request, "Create your owner profile first.")
        return redirect("owner_profile_manage")
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.owner = owner
        expense.save()
        messages.success(request, "Expense added successfully.")
        return redirect("expense_manage")

    expenses = owner.expenses.all()
    return render(
        request,
        "management/expense_manage.html",
        {
            "form": form,
            "expenses": expenses,
            "owner": owner,
            "total_revenue": owner.total_revenue,
            "total_expenses": owner.total_expenses,
            "total_profit": owner.total_profit,
        },
    )




@csrf_exempt
@require_POST
def profile_update_email(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    new_email = (payload.get("new_email") or "").strip().lower()
    verified = payload.get("verified", False)

    if not new_email:
        return HttpResponseBadRequest("new_email is required.")

    if not verified:
        return HttpResponseBadRequest("Email must be verified via OTP first.")

    user = request.user
    if not user.is_authenticated:
        return HttpResponseBadRequest("Authentication required.")

    User = get_user_model()
    if User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
        return HttpResponseBadRequest("This email is already in use.")

    if not _is_otp_verified(request, "profile_email_update", "email", new_email):
        return HttpResponseBadRequest("Email OTP verification required.")

    user.email = new_email
    user.save(update_fields=["email"])

    return JsonResponse({"success": True, "message": "Email updated successfully."})


@require_GET
def vehicle_list(request):
    vehicles = Vehicle.objects.select_related("owner").prefetch_related("images").filter(
        owner__is_verified=True,
        owner__user__is_active=True,
    )
    data = [
        {
            "id": vehicle.id,
            "category": vehicle.category,
            "name": vehicle.name,
            "brand": vehicle.brand,
            "model_year": vehicle.model_year,
            "registration_number": vehicle.registration_number,
            "rent_per_day": float(vehicle.rent_per_day),
            "is_available": vehicle.is_available,
            "owner": vehicle.owner.business_name,
            "photo_url": vehicle.photo_url,
            "photo": vehicle.photo.url if vehicle.photo else "",
            "gallery_images": [img.image.url for img in vehicle.images.all()],
            "owner_photo_url": vehicle.owner.profile_photo_url,
            "owner_photo": vehicle.owner.profile_photo.url if vehicle.owner.profile_photo else "",
            "display_image_url": _vehicle_image_url(vehicle),
        }
        for vehicle in vehicles
    ]
    return JsonResponse({"results": data})


@require_GET
def booking_list(request):
    bookings = Booking.objects.select_related("vehicle", "owner").all()
    data = [
        {
            "id": booking.id,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "customer_email": booking.customer_email,
            "customer_address": booking.customer_address,
            "customer_lpu_id": booking.customer_lpu_id,
            "customer_license_number": booking.customer_license_number,
            "customer_age": booking.customer_age,
            "driving_license_doc": _document_url(booking.driving_license_doc, booking.driving_license_doc_url),
            "student_id_doc": _document_url(booking.student_id_doc, booking.student_id_doc_url),
            "vehicle_id": booking.vehicle_id,
            "vehicle_category": booking.vehicle.category,
            "vehicle_is_available": booking.vehicle.is_available,
            "vehicle": str(booking.vehicle),
            "vehicle_image_url": _vehicle_image_url(booking.vehicle),
            "owner": booking.owner.business_name,
            "start_date": booking.start_date.isoformat(),
            "end_date": booking.end_date.isoformat(),
            "start_time": booking.start_time.strftime("%H:%M") if booking.start_time else "",
            "end_time": booking.end_time.strftime("%H:%M") if booking.end_time else "",
            "rental_unit": booking.rental_unit,
            "rent_per_day": float(booking.vehicle.rent_per_day),
            "duration_days": booking.duration_days,
            "duration_hours": booking.duration_hours,
            "total_price": float(booking.total_price),
            "advance_paid": float(booking.advance_paid),
            "remaining_amount": float(booking.remaining_amount),
            "payment_status": booking.payment_status,
            "payment_method": booking.payment_method,
            "status": booking.status,
        }
        for booking in bookings
    ]
    return JsonResponse({"results": data})


@csrf_exempt
@require_POST
def cancel_booking(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    booking_id = payload.get("booking_id") or payload.get("id")
    customer_email = (payload.get("customer_email") or payload.get("email") or "").strip().lower()
    customer_lpu_id = (payload.get("customer_lpu_id") or payload.get("lpu_id") or "").strip().lower()

    try:
        booking_id = int(booking_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("booking_id is required.")

    booking = get_object_or_404(Booking, id=booking_id)

    booking_email = (booking.customer_email or "").strip().lower()
    booking_lpu = (booking.customer_lpu_id or "").strip().lower()

    # Basic ownership check (this app does not use Django auth for customers).
    if (customer_email and booking_email != customer_email) and (customer_lpu_id and booking_lpu != customer_lpu_id):
        return HttpResponseBadRequest("Booking does not match customer.")

    if booking.status == Booking.Status.CANCELLED:
        return JsonResponse({"cancelled": True, "booking_id": booking.id})

    booking.status = Booking.Status.CANCELLED
    booking.payment_status = Booking.PaymentStatus.PENDING
    booking.advance_paid = Decimal("0.00")
    booking.save(update_fields=["status", "payment_status", "advance_paid", "updated_at"])

    return JsonResponse({"cancelled": True, "booking_id": booking.id})


@csrf_exempt
@require_POST
def feedback_submit(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    message = (payload.get("message") or "").strip()
    rating = payload.get("rating")

    if not message:
        return HttpResponseBadRequest("Message is required.")

    parsed_rating = None
    if rating not in ("", None):
        try:
            parsed_rating = int(rating)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("rating must be a number between 1 and 5.")
        if parsed_rating < 1 or parsed_rating > 5:
            return HttpResponseBadRequest("rating must be between 1 and 5.")

    feedback = Feedback.objects.create(
        name=name[:120],
        email=email[:254],
        rating=parsed_rating,
        message=message,
    )

    to_email = (getattr(settings, "FEEDBACK_TO_EMAIL", "") or "").strip() or getattr(settings, "EMAIL_HOST_USER", "")
    subject = "RoyalWheels - New Feedback"
    body_lines = [
        f"Name: {feedback.name or '-'}",
        f"Email: {feedback.email or '-'}",
        f"Rating: {feedback.rating or '-'}",
        "",
        "Message:",
        feedback.message,
    ]
    body = "\n".join(body_lines)

    if to_email:
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@royalwheels.local"),
                recipient_list=[to_email],
                fail_silently=False,
            )
        except Exception as exc:
            if settings.DEBUG:
                print(f"[DEV FEEDBACK EMAIL FALLBACK] to={to_email} error={exc}")
            # Still return success because feedback is saved in DB.

    return JsonResponse({"saved": True, "message": "Thanks! Your feedback has been submitted."})


@csrf_exempt
@require_POST
def customer_profile_upsert(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    email = (payload.get("email") or "").strip().lower()
    lpu_id = (payload.get("lpu_id") or payload.get("lpuId") or "").strip().lower()

    if not email or "@" not in email:
        return HttpResponseBadRequest("Valid email is required.")

    profile = None
    if lpu_id:
        profile = CustomerProfile.objects.filter(lpu_id__iexact=lpu_id).first()
    if profile is None:
        profile = CustomerProfile.objects.filter(email__iexact=email).first()

    if profile is None:
        profile = CustomerProfile(email=email)

    original_snapshot = {
        "name": profile.name or "",
        "phone": profile.phone or "",
        "age": profile.age,
        "address": profile.address or "",
        "lpu_id": (profile.lpu_id or "").lower(),
        "license_number": profile.license_number or "",
    }

    # Prevent accidental email takeover when lpu_id matches another user
    if profile.email and profile.email.lower() != email:
        profile.email = profile.email.lower()
        if profile.email != email:
            return HttpResponseBadRequest("Email does not match existing profile.")

    next_name = (payload.get("name") or "").strip()[:120]
    next_phone = (payload.get("phone") or "").strip()[:20]
    next_address = (payload.get("address") or "").strip()
    next_license = (payload.get("license_number") or payload.get("license") or "").strip()[:60]

    age = payload.get("age")
    if isinstance(age, str):
        age = age.strip()
    if age in ("", None):
        next_age = None
    else:
        try:
            next_age = int(age)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("age must be a valid number.")
        if next_age < 18:
            return HttpResponseBadRequest("age must be 18 or above.")

    next_lpu_id = lpu_id or None

    is_existing = bool(profile.pk)
    changed_fields = []
    if is_existing:
        if original_snapshot["name"] != next_name:
            changed_fields.append("name")
        if original_snapshot["phone"] != next_phone:
            changed_fields.append("phone")
        if original_snapshot["age"] != next_age:
            changed_fields.append("age")
        if original_snapshot["address"] != next_address:
            changed_fields.append("address")
        if original_snapshot["lpu_id"] != (next_lpu_id or "").lower():
            changed_fields.append("lpu_id")
        if original_snapshot["license_number"] != next_license:
            changed_fields.append("license_number")

        if changed_fields and not (
            _is_otp_verified(request, "customer_profile_update", "email", email)
            or _is_otp_verified(request, "customer_profile_email", "email", email)
        ):
            return HttpResponseBadRequest("Please verify email OTP before saving profile changes.")

    profile.name = next_name
    profile.phone = next_phone
    profile.address = next_address
    profile.license_number = next_license
    profile.age = next_age
    profile.lpu_id = next_lpu_id

    driving_license_raw = payload.get("driving_license_doc") or payload.get("drivingLicenseDoc")
    student_id_raw = payload.get("student_id_doc") or payload.get("studentIdDoc")

    driving_license_doc_url = _upload_data_url_to_cloudinary(
        driving_license_raw,
        f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/customer_docs/licenses",
        "customer_license",
    )
    driving_license_doc = _decode_data_url_file(driving_license_raw, "customer_license")
    if driving_license_doc is None:
        driving_license_doc = None
    if driving_license_doc_url:
        profile.driving_license_doc = None
        profile.driving_license_doc_url = driving_license_doc_url
    elif driving_license_doc is not None:
        profile.driving_license_doc = driving_license_doc
        profile.driving_license_doc_url = ""

    student_id_doc_url = _upload_data_url_to_cloudinary(
        student_id_raw,
        f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/customer_docs/student_ids",
        "customer_student_id",
    )
    student_id_doc = _decode_data_url_file(student_id_raw, "customer_student_id")
    if student_id_doc is None:
        student_id_doc = None
    if student_id_doc_url:
        profile.student_id_doc = None
        profile.student_id_doc_url = student_id_doc_url
    elif student_id_doc is not None:
        profile.student_id_doc = student_id_doc
        profile.student_id_doc_url = ""

    try:
        profile.save()
    except Exception as exc:
        return HttpResponseBadRequest(f"Unable to save profile: {exc}")

    return JsonResponse(
        {
            "saved": True,
            "email": profile.email,
            "lpu_id": profile.lpu_id or "",
            "driving_license_doc": _document_url(profile.driving_license_doc, profile.driving_license_doc_url),
            "student_id_doc": _document_url(profile.student_id_doc, profile.student_id_doc_url),
        }
    )


@csrf_exempt
@require_POST
def customer_profile_update_email(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    current_email = (payload.get("current_email") or payload.get("currentEmail") or "").strip().lower()
    new_email = (payload.get("new_email") or payload.get("newEmail") or "").strip().lower()

    if not current_email or not new_email or "@" not in new_email:
        return HttpResponseBadRequest("current_email and valid new_email are required.")

    if current_email == new_email:
        return JsonResponse({"updated": True, "email": new_email})

    if not _is_otp_verified(request, "customer_profile_email", "email", new_email):
        return HttpResponseBadRequest("Please verify email OTP first.")

    profile = CustomerProfile.objects.filter(email__iexact=current_email).first()
    if profile is None:
        return HttpResponseBadRequest("Customer profile not found.")

    if CustomerProfile.objects.filter(email__iexact=new_email).exclude(id=profile.id).exists():
        return HttpResponseBadRequest("A user with this email already exists.")

    profile.email = new_email
    profile.save(update_fields=["email", "updated_at"])
    return JsonResponse({"updated": True, "email": new_email})


def _parse_money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount >= 0 else None


def _parse_iso_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_iso_time(value):
    try:
        return datetime.strptime(str(value), "%H:%M").time()
    except (TypeError, ValueError):
        return None


def _decode_data_url_file(data_url, prefix):
    if not data_url or not isinstance(data_url, str) or ";base64," not in data_url:
        return None

    header, encoded = data_url.split(";base64,", 1)
    mime = header.split(":", 1)[-1].lower()
    extension = "bin"
    if mime in {"image/jpeg", "image/jpg"}:
        extension = "jpg"
    elif mime == "image/png":
        extension = "png"
    elif mime == "application/pdf":
        extension = "pdf"

    try:
        decoded = base64.b64decode(encoded)
    except (ValueError, TypeError):
        return None

    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.{extension}"
    return ContentFile(decoded, name=filename)


@csrf_exempt
@require_POST
def otp_send(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    purpose = (payload.get("purpose") or "").strip().lower()
    channel = (payload.get("channel") or "").strip().lower()
    target = (payload.get("target") or "").strip()

    if not purpose or channel not in {"email", "phone"} or not target:
        return HttpResponseBadRequest("purpose, channel(email/phone) and target are required.")

    if channel == "email":
        target = target.lower()

    if channel == "phone":
        target = _normalize_indian_phone(target)
        if not target:
            return HttpResponseBadRequest("Enter a valid Indian mobile number.")

    otp_id, code = _create_otp(request, purpose, channel, target)

    if channel == "email":
        sent, message = _send_email_otp(target, code)
    else:
        sent, message = _send_phone_otp(target, code)

    if not sent:
        return HttpResponseBadRequest(message)

    return JsonResponse({"otp_id": otp_id, "message": message})


@csrf_exempt
@require_POST
def otp_verify(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    otp_id = (payload.get("otp_id") or "").strip()
    otp_code = (payload.get("otp_code") or "").strip()

    if not otp_id or not otp_code:
        return HttpResponseBadRequest("otp_id and otp_code are required.")

    store = _otp_session_store(request)
    record = store.get(otp_id)
    if not record:
        return HttpResponseBadRequest("OTP not found.")

    if int(time.time()) > int(record.get("expires_at") or 0):
        return HttpResponseBadRequest("OTP has expired.")

    if str(record.get("code")) != otp_code:
        return HttpResponseBadRequest("Invalid OTP.")

    record["verified"] = True
    store[otp_id] = record
    request.session["otp_store"] = store
    _mark_otp_verified(request, record["purpose"], record["channel"], record["target"])

    return JsonResponse({"verified": True, "message": "OTP verified."})


@csrf_exempt
@require_POST
def razorpay_create_order(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    booking_id = payload.get("booking_id")
    if not booking_id:
        return HttpResponseBadRequest("booking_id is required.")

    booking = get_object_or_404(Booking, id=booking_id)
    if booking.payment_status == Booking.PaymentStatus.PAID:
        return HttpResponseBadRequest("Booking is already paid.")

    currency = (getattr(settings, "RAZORPAY_CURRENCY", "INR") or "INR").strip().upper()
    try:
        amount_paise = int((booking.total_price * 100).quantize(Decimal("1")))
    except Exception:
        return HttpResponseBadRequest("Invalid booking amount.")

    try:
        order = _razorpay_create_order(
            amount_paise=amount_paise,
            receipt=f"booking_{booking.id}",
            currency=currency,
            notes={"booking_id": str(booking.id)},
        )
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    except urllib.error.HTTPError as exc:
        try:
            message = exc.read().decode("utf-8")
        except Exception:
            message = str(exc)
        return HttpResponseBadRequest(f"Razorpay error: {message}")
    except Exception as exc:
        return HttpResponseBadRequest(f"Unable to create payment order: {exc}")

    order_id = (order.get("id") or "").strip()
    if not order_id:
        return HttpResponseBadRequest("Razorpay order creation failed.")

    booking.razorpay_order_id = order_id
    booking.payment_method = "razorpay"
    booking.save(update_fields=["razorpay_order_id", "payment_method", "updated_at"])

    return JsonResponse(
        {
            "booking_id": booking.id,
            "key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
            "order_id": order_id,
            "amount": amount_paise,
            "currency": currency,
        }
    )


@csrf_exempt
@require_POST
def razorpay_verify_payment(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    booking_id = payload.get("booking_id")
    order_id = (payload.get("razorpay_order_id") or "").strip()
    payment_id = (payload.get("razorpay_payment_id") or "").strip()
    signature = (payload.get("razorpay_signature") or "").strip()

    if not booking_id or not order_id or not payment_id or not signature:
        return HttpResponseBadRequest("booking_id, razorpay_order_id, razorpay_payment_id and razorpay_signature are required.")

    booking = get_object_or_404(Booking, id=booking_id)
    if booking.razorpay_order_id and booking.razorpay_order_id != order_id:
        return HttpResponseBadRequest("Order ID does not match booking.")

    expected = _razorpay_expected_signature(order_id=order_id, payment_id=payment_id)
    if not hmac.compare_digest(str(expected), str(signature)):
        return HttpResponseBadRequest("Invalid payment signature.")

    booking.razorpay_order_id = order_id
    booking.razorpay_payment_id = payment_id
    booking.razorpay_signature = signature
    booking.payment_method = "razorpay"
    booking.payment_status = Booking.PaymentStatus.PAID
    booking.advance_paid = booking.total_price
    booking.save(
        update_fields=[
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "payment_method",
            "payment_status",
            "advance_paid",
            "updated_at",
        ]
    )

    return JsonResponse({"paid": True, "booking_id": booking.id})


@csrf_exempt
@require_POST
def add_expense(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    owner_id = payload.get("owner_id")
    title = payload.get("title")
    amount = _parse_money(payload.get("amount"))

    if not owner_id or not title or amount is None:
        return HttpResponseBadRequest("owner_id, title and a valid amount are required.")

    owner = get_object_or_404(OwnerProfile, id=owner_id)
    expense = Expense.objects.create(
        owner=owner,
        title=title,
        amount=amount,
        notes=payload.get("notes", ""),
    )

    return JsonResponse(
        {
            "id": expense.id,
            "owner": owner.business_name,
            "title": expense.title,
            "amount": float(expense.amount),
            "spent_on": expense.spent_on.isoformat(),
        },
        status=201,
    )


@csrf_exempt
@require_POST
def create_booking(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    vehicle_id = payload.get("vehicle_id")
    customer_name = (payload.get("customer_name") or "").strip()
    customer_phone = (payload.get("customer_phone") or "").strip()
    customer_email = (payload.get("customer_email") or "").strip()
    customer_address = (payload.get("customer_address") or "").strip()
    customer_lpu_id = (payload.get("customer_lpu_id") or "").strip()
    customer_license_number = (payload.get("customer_license_number") or "").strip()
    customer_age = payload.get("customer_age")
    payment_method = (payload.get("payment_method") or "").strip().lower()
    rental_unit = (payload.get("rental_unit") or Booking.RentalUnit.DAY).strip().lower()
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")
    total_price = _parse_money(payload.get("total_price"))
    driving_license_raw = payload.get("driving_license_doc")
    student_id_raw = payload.get("student_id_doc")

    driving_license_doc_url = _upload_data_url_to_cloudinary(
        driving_license_raw,
        f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/booking_docs/licenses",
        "license",
    )
    student_id_doc_url = _upload_data_url_to_cloudinary(
        student_id_raw,
        f"{getattr(settings, 'CLOUDINARY_FOLDER', 'royalwheels')}/booking_docs/student_ids",
        "student_id",
    )

    driving_license_doc = _decode_data_url_file(driving_license_raw, "license")
    student_id_doc = _decode_data_url_file(student_id_raw, "student_id")

    # If user previously uploaded docs in DB, allow booking without sending base64 docs again.
    if (driving_license_doc is None and not driving_license_doc_url) or (student_id_doc is None and not student_id_doc_url):
        profile = None
        lookup_email = (customer_email or "").strip().lower()
        lookup_lpu = (customer_lpu_id or "").strip().lower()
        if lookup_lpu:
            profile = CustomerProfile.objects.filter(lpu_id__iexact=lookup_lpu).first()
        if profile is None and lookup_email:
            profile = CustomerProfile.objects.filter(email__iexact=lookup_email).first()
        if profile:
            driving_license_doc = driving_license_doc or profile.driving_license_doc
            student_id_doc = student_id_doc or profile.student_id_doc
            driving_license_doc_url = driving_license_doc_url or profile.driving_license_doc_url
            student_id_doc_url = student_id_doc_url or profile.student_id_doc_url

    if isinstance(customer_age, str):
        customer_age = customer_age.strip()
    if customer_age in ("", None):
        customer_age = None
    else:
        try:
            customer_age = int(customer_age)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("customer_age must be a valid number.")
        if customer_age < 18:
            return HttpResponseBadRequest("customer_age must be 18 or above.")

    if (
        not vehicle_id
        or not customer_name
        or not customer_phone
        or not customer_email
        or not customer_address
        or not customer_lpu_id
        or not customer_license_number
        or customer_age is None
        or not start_date
        or not end_date
        or (driving_license_doc is None and not driving_license_doc_url)
        or (student_id_doc is None and not student_id_doc_url)
    ):
        return HttpResponseBadRequest("Complete profile and both documents are required before booking.")

    if rental_unit not in {Booking.RentalUnit.DAY, Booking.RentalUnit.HOUR}:
        return HttpResponseBadRequest("Invalid rental_unit. Use 'day' or 'hour'.")

    parsed_start_date = _parse_iso_date(start_date)
    parsed_end_date = _parse_iso_date(end_date)
    if not parsed_start_date or not parsed_end_date:
        return HttpResponseBadRequest("start_date and end_date must be valid dates (YYYY-MM-DD).")
    if parsed_end_date < parsed_start_date:
        return HttpResponseBadRequest("end_date must be same or after start_date.")

    parsed_start_time = None
    parsed_end_time = None

    vehicle = get_object_or_404(
        Vehicle.objects.select_related("owner"),
        id=vehicle_id,
        owner__is_verified=True,
        owner__user__is_active=True,
    )

    if not vehicle.is_available:
        return HttpResponseBadRequest("Vehicle is not available.")

    if rental_unit == Booking.RentalUnit.DAY:
        total_days = (parsed_end_date - parsed_start_date).days
        if total_days <= 0:
            return HttpResponseBadRequest("For daily booking, end_date must be after start_date.")
        computed_total = Decimal(total_days) * vehicle.rent_per_day
    else:
        parsed_start_time = _parse_iso_time(start_time)
        parsed_end_time = _parse_iso_time(end_time)
        if not parsed_start_time or not parsed_end_time:
            return HttpResponseBadRequest("For hourly booking, start_time and end_time are required (HH:MM).")
        if parsed_start_date != parsed_end_date:
            return HttpResponseBadRequest("Hourly booking currently supports same-day booking only.")

        start_dt = datetime.combine(parsed_start_date, parsed_start_time)
        end_dt = datetime.combine(parsed_end_date, parsed_end_time)
        if end_dt <= start_dt:
            return HttpResponseBadRequest("For hourly booking, end_time must be after start_time.")

        total_hours = math.ceil((end_dt - start_dt).total_seconds() / 3600)
        hourly_rate = (vehicle.rent_per_day / Decimal("24")).quantize(Decimal("0.01"))
        computed_total = Decimal(total_hours) * hourly_rate

    if total_price is not None and abs(total_price - computed_total) > Decimal("0.5"):
        return HttpResponseBadRequest("Submitted total does not match calculated booking total.")

    payment_status = Booking.PaymentStatus.PENDING
    if payment_method in {"cash", "cod"}:
        payment_method = "cash"
        payment_status = Booking.PaymentStatus.PENDING
    elif payment_method == "upi":
        payment_method = "upi"
        payment_status = Booking.PaymentStatus.PENDING
    elif payment_method == "card":
        payment_method = "card"
        payment_status = Booking.PaymentStatus.PENDING

    try:
        booking = Booking.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            customer_address=customer_address,
            customer_lpu_id=customer_lpu_id,
            customer_license_number=customer_license_number,
            customer_age=customer_age,
            owner=vehicle.owner,
            vehicle=vehicle,
            rental_unit=rental_unit,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            total_price=computed_total,
            payment_status=payment_status,
            payment_method=payment_method,
            status=Booking.Status.PENDING,
            driving_license_doc=driving_license_doc,
            driving_license_doc_url=driving_license_doc_url or "",
            student_id_doc=student_id_doc,
            student_id_doc_url=student_id_doc_url or "",
        )
    except OperationalError:
        return HttpResponseBadRequest(
            "Database schema is out of date. Run: python backend/manage.py migrate"
        )

    return JsonResponse(
        {
            "id": booking.id,
            "status": booking.status,
            "vehicle": f"{vehicle.brand} {vehicle.name}",
        },
        status=201,
    )


@csrf_exempt
@require_POST
def customer_signup(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    lpu_id = (payload.get("lpu_id") or payload.get("lpuId") or "").strip().lower()

    if not name or not email or not password:
        return HttpResponseBadRequest("Name, email and password are required.")

    if CustomerProfile.objects.filter(email__iexact=email).exists():
        return HttpResponseBadRequest("An account with this email already exists.")
    
    if lpu_id and CustomerProfile.objects.filter(lpu_id__iexact=lpu_id).exists():
        return HttpResponseBadRequest("An account with this LPU ID already exists.")

    if not _is_otp_verified(request, "customer_signup", "email", email):
        return HttpResponseBadRequest("Please verify your email OTP before signup.")

    profile = CustomerProfile.objects.create(
        name=name,
        email=email,
        password=make_password(password),
        phone=(payload.get("phone") or "").strip(),
        age=payload.get("age"),
        address=(payload.get("address") or "").strip(),
        lpu_id=lpu_id or None,
        license_number=(payload.get("license") or "").strip(),
    )

    return JsonResponse({"success": True, "message": "Signup successful! Please login."})


@csrf_exempt
@require_POST
def customer_login(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    identifier = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not identifier or not password:
        return HttpResponseBadRequest("Email/ID and password are required.")

    profile = CustomerProfile.objects.filter(
        Q(email__iexact=identifier) | Q(lpu_id__iexact=identifier)
    ).first()

    if profile and (check_password(password, profile.password) or profile.password == password):
        # Auto-upgrade plain-text password if found
        if profile.password == password and not password.startswith("pbkdf2_"):
             profile.password = make_password(password)
             profile.save(update_fields=["password"])

        return JsonResponse({
            "success": True,
            "user": {
                "name": profile.name,
                "email": profile.email,
                "phone": profile.phone,
                "age": profile.age,
                "address": profile.address,
                "license": profile.license_number,
                "lpuId": profile.lpu_id or "",
                "profilePhoto": profile.driving_license_doc_url,
            }
        })
    else:
        return HttpResponseBadRequest("Invalid email/ID or password.")


@csrf_exempt
@require_POST
def reset_customer_password(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return HttpResponseBadRequest("Email and new password are required.")

    if not _is_otp_verified(request, "customer_forgot", "email", email):
        return HttpResponseBadRequest("Please verify reset email OTP first.")

    profile = CustomerProfile.objects.filter(email__iexact=email).first()
    if not profile:
        return HttpResponseBadRequest("Account not found.")

    profile.password = make_password(password)
    profile.save(update_fields=["password", "updated_at"])

    return JsonResponse({"success": True, "message": "Password reset successfully."})

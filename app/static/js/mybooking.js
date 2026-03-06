let bookings = [];
let vehiclesCache = null;
let activeFeedbackBooking = null;

const container = document.getElementById("bookingsContainer");
const sortSelect = document.getElementById("sortSelect");
const feedbackModal = document.getElementById("feedbackModal");
const feedbackTitle = document.getElementById("feedbackTitle");
const feedbackSubtitle = document.getElementById("feedbackSubtitle");
const feedbackMessage = document.getElementById("feedbackMessage");
const submitFeedbackBtn = document.getElementById("submitFeedback");

function getActiveCustomer() {
  return JSON.parse(localStorage.getItem("loggedCustomer") || "null");
}

function customerBookingKey(customer) {
  const lpu = String(customer?.lpuId || "").trim().toLowerCase();
  const email = String(customer?.email || "").trim().toLowerCase();
  return lpu || email;
}

function renderBookings() {
  container.innerHTML = "";

  const visibleBookings = bookings.filter((booking) => {
    const statusLower = String(booking.status || "").trim().toLowerCase();
    if (statusLower === "cancelled") return true;

    const paymentStatus = String(booking.payment_status || booking.paymentStatus || "pending").toLowerCase();
    const paymentMethod = String(booking.payment_method || booking.paymentMethod || "").toLowerCase();

    // Hide unfinished Razorpay/UPI attempts from My Bookings.
    if ((paymentMethod === "upi" || paymentMethod === "razorpay") && paymentStatus === "pending") {
      return false;
    }

    return true;
  });

  if (visibleBookings.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <h2>No Bookings Yet</h2>
        <p>You haven't made any bookings yet.</p>
        <a href="Car.html">Explore Vehicles</a>
      </div>
    `;
    return;
  }

  visibleBookings.forEach((booking) => {
    const bookingVehicle = String(booking.vehicle || "");
    const type = booking.type || (bookingVehicle.toLowerCase().includes("bike") ? "Bike" : "Car");
    const image =
      booking.image ||
      booking.vehicle_image_url ||
      booking.display_image_url ||
      "/static/assets/logo.jpg";
    const pickup = booking.pickup || booking.start_date || "-";
    const returnDate = booking.returnDate || booking.end_date || "-";
    const pickupTime = booking.pickupTime || booking.start_time || "";
    const returnTime = booking.returnTime || booking.end_time || "";
    const rentalUnit = booking.rental_unit || booking.rentalUnit || "day";
    const pickupDisplay = pickupTime ? `${pickup} ${pickupTime}` : pickup;
    const returnDisplay = returnTime ? `${returnDate} ${returnTime}` : returnDate;
    const rentPerDay = Number(booking.rent_per_day || booking.pricePerDay || 0);
    const start = pickup && pickup !== "-" ? new Date(pickupTime ? `${pickup}T${pickupTime}` : pickup) : null;
    const end = returnDate && returnDate !== "-" ? new Date(returnTime ? `${returnDate}T${returnTime}` : returnDate) : null;
    const days = start && end ? Math.max(Math.ceil((end - start) / (1000 * 60 * 60 * 24)), 0) : 0;
    const computedTotal = rentPerDay && rentalUnit !== "hour" && days ? rentPerDay * days : null;
    const total = computedTotal ?? booking.total ?? booking.total_price ?? 0;
    const status = String(booking.status || "pending");
    const statusLabel = status.charAt(0).toUpperCase() + status.slice(1);
    const statusLower = status.trim().toLowerCase();
    const paymentStatus = String(booking.payment_status || booking.paymentStatus || "pending").toLowerCase();
    const paymentLabel = paymentStatus === "paid" ? "Paid" : "Pending";
    const paymentMethodRaw = String(booking.payment_method || booking.paymentMethod || "").toLowerCase();
    const paymentMethodLabel =
      paymentMethodRaw === "cash" || paymentMethodRaw === "cod"
        ? "Pay at Pickup"
        : paymentMethodRaw === "razorpay" || paymentMethodRaw === "upi"
          ? "UPI (Razorpay)"
          : paymentMethodRaw === "card"
            ? "Card"
            : paymentMethodRaw
              ? paymentMethodRaw.toUpperCase()
              : "Pay at Pickup";

    const paymentDisplay =
      statusLower === "cancelled"
        ? "Cancelled"
        : (paymentMethodLabel === "UPI (Razorpay)" && paymentLabel === "Pending")
          ? "UPI (Razorpay)"
          : (paymentMethodLabel === "Pay at Pickup" && paymentLabel === "Pending")
            ? "Pay at Pickup"
          : `${paymentMethodLabel} (${paymentLabel})`;
    const vehicleId = Number(booking.vehicle_id || booking.vehicleId || 0);
    const vehicleAvailable = booking.vehicle_is_available ?? booking.is_available ?? true;

    const feedbackKey = customerBookingKey(getActiveCustomer() || {});
    const feedbackSentList = JSON.parse(localStorage.getItem(feedbackKey ? `feedbackSent:${feedbackKey}` : "feedbackSent") || "[]");
    const feedbackSent = feedbackSentList.includes(Number(booking.id));

    const bookingCard = `
      <div class="booking-card">
        <div class="left-section">
          <img src="${image}" class="booking-image" alt="${bookingVehicle}">
          <div class="booking-info">
            <h2>${bookingVehicle}</h2>
            <p><strong>Rental:</strong> ${pickupDisplay} to ${returnDisplay}</p>
            <p><strong>Type:</strong> ${type}</p>
            <p><strong>Plan:</strong> ${rentalUnit === "hour" ? "Hourly" : "Daily"}</p>
            <p><strong>Payment:</strong> ${paymentDisplay}</p>
          </div>
        </div>
        <div class="right-section">
          <p class="price">Rs ${total}</p>
          <p class="status">${statusLabel}</p>
          <div class="booking-actions">
            <button
              class="action-btn rerent"
              data-action="rerent"
              data-booking-id="${booking.id}"
              data-vehicle-id="${vehicleId}"
              data-vehicle-name="${encodeURIComponent(bookingVehicle)}"
              data-vehicle-image="${encodeURIComponent(image)}"
              data-vehicle-type="${encodeURIComponent(type)}"
              data-vehicle-price="${encodeURIComponent(String(rentPerDay || 0))}"
              data-vehicle-available="${vehicleAvailable ? "1" : "0"}"
              ${vehicleId ? "" : "disabled"}
            >
              Re-rent
            </button>
            <button
              class="action-btn ${feedbackSent ? "ghost" : "feedback"}"
              data-action="feedback"
              data-booking-id="${booking.id}"
              ${feedbackSent ? "disabled" : ""}
            >
              ${feedbackSent ? "Feedback Sent" : "Feedback"}
            </button>
          </div>
        </div>
      </div>
    `;

    container.innerHTML += bookingCard;
  });
}

function sortBookings(value) {
  if (value === "price") {
    bookings.sort((a, b) => Number(a.total || a.total_price || 0) - Number(b.total || b.total_price || 0));
  }

  if (value === "date") {
    bookings.sort((a, b) => new Date(a.pickup || a.start_date) - new Date(b.pickup || b.start_date));
  }

  if (value === "name") {
    // "Sort by Bikes" (bikes first), then name.
    const rank = (item) => (String(item.type || "").toLowerCase() === "bike" ? 0 : 1);
    bookings.sort((a, b) => {
      const diff = rank(a) - rank(b);
      if (diff !== 0) return diff;
      return String(a.vehicle || "").localeCompare(String(b.vehicle || ""));
    });
  }

  if (value === "type") {
    // "Sort by cars" (cars first), then name.
    const rank = (item) => (String(item.type || "").toLowerCase() === "car" ? 0 : 1);
    bookings.sort((a, b) => {
      const diff = rank(a) - rank(b);
      if (diff !== 0) return diff;
      return String(a.vehicle || "").localeCompare(String(b.vehicle || ""));
    });
  }

  renderBookings();
}

async function loadBookings() {
  const activeRole = localStorage.getItem("activeRole");
  const customer = getActiveCustomer();
  if (activeRole !== "customer" || !customer) {
    alert("Please login first to view your bookings.");
    window.location.href = "/login.html";
    return;
  }

  const key = customerBookingKey(customer);
  if (!key) {
    bookings = [];
    renderBookings();
    return;
  }

  const emailKey = String(customer.email || "").trim().toLowerCase();
  const lpuKey = String(customer.lpuId || "").trim().toLowerCase();

  try {
    const response = await fetch("/api/bookings/");
    if (!response.ok) {
      throw new Error("Unable to fetch bookings");
    }

    const payload = await response.json();
    const allBookings = Array.isArray(payload.results) ? payload.results : [];
    bookings = allBookings
      .filter((booking) => {
        const bookingEmail = String(booking.customer_email || "").trim().toLowerCase();
        const bookingLpu = String(booking.customer_lpu_id || "").trim().toLowerCase();
        return (emailKey && bookingEmail === emailKey) || (lpuKey && bookingLpu === lpuKey);
      })
      .map((booking) => ({
        ...booking,
        pickup: booking.start_date,
        returnDate: booking.end_date,
        pickupTime: booking.start_time,
        returnTime: booking.end_time,
        total: booking.total_price,
        rent_per_day: booking.rent_per_day,
        type:
          booking.vehicle_category
            ? String(booking.vehicle_category).toLowerCase() === "bike"
              ? "Bike"
              : "Car"
            : String(booking.vehicle || "").toLowerCase().includes("bike")
              ? "Bike"
              : "Car",
      }));

    localStorage.setItem(`confirmedBookings:${key}`, JSON.stringify(bookings));
    renderBookings();
  } catch (error) {
    bookings = JSON.parse(localStorage.getItem(`confirmedBookings:${key}`) || "[]");
    renderBookings();
  }
}

sortSelect?.addEventListener("change", function () {
  sortBookings(this.value);
});

async function ensureVehiclesCache() {
  if (vehiclesCache) return vehiclesCache;
  try {
    const response = await fetch("/api/vehicles/");
    if (!response.ok) throw new Error("Unable to fetch vehicles");
    const data = await response.json();
    const results = Array.isArray(data.results) ? data.results : [];
    vehiclesCache = new Map(results.map((v) => [Number(v.id), v]));
  } catch (_) {
    vehiclesCache = new Map();
  }
  return vehiclesCache;
}

function openFeedbackModal(booking) {
  activeFeedbackBooking = booking;
  if (feedbackTitle) feedbackTitle.textContent = "Share Feedback";
  if (feedbackSubtitle) feedbackSubtitle.textContent = `For: ${booking.vehicle || "your booking"}`;
  if (feedbackMessage) feedbackMessage.value = "";
  document.querySelectorAll('input[name="rating"]').forEach((el) => (el.checked = false));
  feedbackModal?.classList.add("is-open");
  feedbackModal?.setAttribute("aria-hidden", "false");
  setTimeout(() => feedbackMessage?.focus(), 0);
}

function closeFeedbackModal() {
  activeFeedbackBooking = null;
  feedbackModal?.classList.remove("is-open");
  feedbackModal?.setAttribute("aria-hidden", "true");
}

function getSelectedRating() {
  const selected = document.querySelector('input[name="rating"]:checked');
  return selected ? Number(selected.value) : 0;
}

async function submitFeedback() {
  const customer = getActiveCustomer();
  if (!customer) {
    alert("Please login first.");
    window.location.href = "/login.html";
    return;
  }

  if (!activeFeedbackBooking) {
    alert("Booking not found.");
    return;
  }

  const rating = getSelectedRating();
  const message = String(feedbackMessage?.value || "").trim();

  if (!rating || rating < 1 || rating > 5) {
    alert("Please select a star rating.");
    return;
  }
  if (!message) {
    alert("Please write your feedback.");
    return;
  }

  const detailsHeader = [
    `Booking ID: ${activeFeedbackBooking.id}`,
    `Vehicle: ${activeFeedbackBooking.vehicle || "-"}`,
    `Payment: ${String(activeFeedbackBooking.payment_status || "-")}`,
    "",
  ].join("\n");

  const payload = {
    name: String(customer.name || "").trim(),
    email: String(customer.email || "").trim(),
    rating,
    message: detailsHeader + message,
  };

  submitFeedbackBtn.disabled = true;
  try {
    const response = await fetch("/api/feedback/submit/", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(text || "Unable to submit feedback.");
    }

    const key = customerBookingKey(customer);
    const storageKey = key ? `feedbackSent:${key}` : "feedbackSent";
    const sent = JSON.parse(localStorage.getItem(storageKey) || "[]");
    if (!sent.includes(Number(activeFeedbackBooking.id))) {
      sent.push(Number(activeFeedbackBooking.id));
      localStorage.setItem(storageKey, JSON.stringify(sent));
    }

    alert("Thanks! Your feedback has been sent.");
    closeFeedbackModal();
    renderBookings();
  } catch (error) {
    alert(error.message || "Unable to submit feedback.");
  } finally {
    submitFeedbackBtn.disabled = false;
  }
}

// Events
container?.addEventListener("click", async (event) => {
  const button = event.target?.closest?.("button[data-action]");
  if (!button) return;

  const action = button.getAttribute("data-action");
  const bookingId = Number(button.getAttribute("data-booking-id") || "0");
  const booking = bookings.find((b) => Number(b.id) === bookingId);

  if (action === "feedback") {
    if (!booking) {
      alert("Booking not found.");
      return;
    }
    openFeedbackModal(booking);
    return;
  }

  if (action === "rerent") {
    const vehicleId = Number(button.getAttribute("data-vehicle-id") || "0");
    if (!vehicleId) {
      alert("Vehicle information not found for this booking.");
      return;
    }

    const cache = await ensureVehiclesCache();
    const vehicle = cache.get(vehicleId);
    const isAvailable =
      (vehicle ? Boolean(vehicle.is_available) : null) ??
      (button.getAttribute("data-vehicle-available") === "1");

    if (!isAvailable) {
      alert("This vehicle is not available right now.");
      return;
    }

    const selectedVehicle = {
      vehicleId,
      vehicle: decodeURIComponent(button.getAttribute("data-vehicle-name") || ""),
      image: decodeURIComponent(button.getAttribute("data-vehicle-image") || ""),
      pricePerDay: Number(button.getAttribute("data-vehicle-price") || "0") || Number(vehicle?.rent_per_day || 0),
      type: decodeURIComponent(button.getAttribute("data-vehicle-type") || "") || (vehicle?.category === "bike" ? "Bike" : "Car"),
    };

    localStorage.setItem("selectedVehicle", JSON.stringify(selectedVehicle));
    window.location.href = "/Book_now.html";
  }
});

document.getElementById("closeFeedbackModal")?.addEventListener("click", closeFeedbackModal);
document.getElementById("cancelFeedback")?.addEventListener("click", closeFeedbackModal);
feedbackModal?.addEventListener("click", (event) => {
  if (event.target === feedbackModal) closeFeedbackModal();
});
submitFeedbackBtn?.addEventListener("click", submitFeedback);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeFeedbackModal();
});

loadBookings();

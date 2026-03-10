let activeVehicle = {
  vehicleId: 0,
  vehicle: "BMW X7",
  image: "/static/assets/BMW.png",
  pricePerDay: 4000,
  pricePerHour: 167,
  type: "Car"
};

function normalizeImageUrl(url) {
  const raw = String(url || "").trim();
  if (!raw) {
    return "";
  }
  if (raw.startsWith("http://") || raw.startsWith("https://") || raw.startsWith("/")) {
    return raw;
  }
  if (raw.startsWith("../assets/")) {
    return `/static/assets/${raw.slice("../assets/".length)}`;
  }
  if (raw.startsWith("assets/")) {
    return `/static/${raw}`;
  }
  return raw;
}

function attachNavbarActions() {
  const adminBtn = document.querySelector(".nav-actions .btn-outline");
  const loginBtn = document.querySelector(".nav-actions .btn-primary");

  adminBtn?.addEventListener("click", () => {
    window.location.href = "/admin-login/";
  });

  loginBtn?.addEventListener("click", () => {
    window.location.href = "/login.html";
  });
}

function populateVehicle() {
  const selected = JSON.parse(localStorage.getItem("selectedVehicle") || "null");
  if (selected && selected.vehicle && selected.pricePerDay) {
    activeVehicle = selected;
  }

  activeVehicle.image = normalizeImageUrl(activeVehicle.image) || "/static/assets/logo.jpg";

  if (!activeVehicle.pricePerHour) {
    activeVehicle.pricePerHour = Math.max(Math.ceil(Number(activeVehicle.pricePerDay || 0) / 24), 1);
  }

  const imageEl = document.querySelector(".vehicle-image");
  const titleEl = document.querySelector(".vehicle-title");
  const priceEl = document.querySelector(".booking-box .price");

  if (imageEl) {
    imageEl.src = activeVehicle.image;
    imageEl.alt = activeVehicle.vehicle;
  }

  if (titleEl) {
    titleEl.textContent = activeVehicle.vehicle;
  }

  if (priceEl) {
    priceEl.innerHTML = `Rs ${activeVehicle.pricePerDay} <span>/ day</span>`;
  }
}

function calculateTotal() {
  const pickup = document.getElementById("pickup");
  const returnDate = document.getElementById("return");
  const bookingType = document.getElementById("bookingType");
  const pickupTime = document.getElementById("pickupTime");
  const returnTime = document.getElementById("returnTime");
  const totalPrice = document.getElementById("totalPrice");
  const priceEl = document.querySelector(".booking-box .price");
  if (!pickup || !returnDate || !totalPrice) {
    return;
  }

  const mode = bookingType?.value || "day";
  if (priceEl) {
    priceEl.innerHTML =
      mode === "hour"
        ? `Rs ${activeVehicle.pricePerHour} <span>/ hour</span>`
        : `Rs ${activeVehicle.pricePerDay} <span>/ day</span>`;
  }

  if (!pickup.value || !returnDate.value) {
    totalPrice.textContent = "0";
    return;
  }

  if (mode === "hour") {
    if (!pickupTime?.value || !returnTime?.value) {
      totalPrice.textContent = "0";
      return;
    }
    const start = new Date(`${pickup.value}T${pickupTime.value}`);
    const end = new Date(`${returnDate.value}T${returnTime.value}`);
    const hours = (end - start) / (1000 * 60 * 60);

    if (hours > 0) {
      const billedHours = Math.ceil(hours);
      totalPrice.textContent = String(billedHours * activeVehicle.pricePerHour);
    } else {
      totalPrice.textContent = "0";
    }
    return;
  }

  const start = new Date(pickup.value);
  const end = new Date(returnDate.value);
  const days = (end - start) / (1000 * 60 * 60 * 24);

  if (days > 0) {
    totalPrice.textContent = String(days * activeVehicle.pricePerDay);
  } else {
    totalPrice.textContent = "0";
  }
}

function handleBooking() {
  const pickup = document.getElementById("pickup");
  const returnDate = document.getElementById("return");
  const bookingType = document.getElementById("bookingType");
  const pickupTime = document.getElementById("pickupTime");
  const returnTime = document.getElementById("returnTime");
  if (!pickup || !returnDate) {
    return;
  }

  if (!activeVehicle.vehicleId) {
    alert("Vehicle data not found. Please book again from Cars/Bikes page.");
    return;
  }

  const user = JSON.parse(localStorage.getItem("loggedCustomer") || "null");
  if (!user) {
    alert("Please login as user first.");
    window.location.href = "/login.html";
    return;
  }

  if (
    !user.name ||
    !user.phone ||
    !user.email ||
    !user.address ||
    !user.lpuId ||
    !user.license ||
    !user.age
  ) {
    alert("Please complete your profile details before booking.");
    window.location.href = "/profile.html";
    return;
  }

  if (!user.drivingLicenseDoc || !user.studentIdDoc) {
    alert("Please upload Driving License and College ID Card in Profile before booking.");
    window.location.href = "/profile.html";
    return;
  }

  if (!pickup.value || !returnDate.value) {
    alert("Please select pickup and return dates.");
    return;
  }

  const mode = bookingType?.value || "day";
  let totalAmount = 0;
  let startTime = "";
  let endTime = "";

  if (mode === "hour") {
    if (!pickupTime?.value || !returnTime?.value) {
      alert("Please select pickup and return time for hourly booking.");
      return;
    }
    if (pickup.value !== returnDate.value) {
      alert("Hourly booking currently supports same-day booking only.");
      return;
    }

    const hours =
      (new Date(`${returnDate.value}T${returnTime.value}`) -
        new Date(`${pickup.value}T${pickupTime.value}`)) /
      (1000 * 60 * 60);
    if (hours <= 0) {
      alert("Return time must be after pickup time.");
      return;
    }

    totalAmount = Math.ceil(hours) * activeVehicle.pricePerHour;
    startTime = pickupTime.value;
    endTime = returnTime.value;
  } else {
    const days = (new Date(returnDate.value) - new Date(pickup.value)) / (1000 * 60 * 60 * 24);
    if (days <= 0) {
      alert("Return date must be after pickup date.");
      return;
    }
    totalAmount = days * activeVehicle.pricePerDay;
  }

  const bookingData = {
    vehicleId: activeVehicle.vehicleId,
    vehicle: activeVehicle.vehicle,
    image: activeVehicle.image,
    type: activeVehicle.type || "Car",
    customerName: String(user.name).trim(),
    customerPhone: String(user.phone).trim(),
    customerEmail: String(user.email).trim(),
    customerAddress: String(user.address).trim(),
    customerLpuId: String(user.lpuId).trim(),
    customerLicenseNumber: String(user.license).trim(),
    customerAge: Number(user.age),
    drivingLicenseDoc: user.drivingLicenseDoc,
    studentIdDoc: user.studentIdDoc,
    pricePerDay: activeVehicle.pricePerDay,
    pricePerHour: activeVehicle.pricePerHour,
    rentalUnit: mode,
    pickup: pickup.value,
    returnDate: returnDate.value,
    pickupTime: startTime,
    returnTime: endTime,
    total: totalAmount
  };

  localStorage.setItem("pendingBooking", JSON.stringify(bookingData));
  window.location.href = "/payment.html";
}

function setMinDateToToday() {
  const today = new Date().toISOString().split("T")[0];
  const allDateInputs = document.querySelectorAll('input[type="date"]');

  allDateInputs.forEach((input) => {
    input.setAttribute("min", today);
  });
}

function setupDateValidation() {
  const pickup = document.getElementById("pickup");
  const returnDate = document.getElementById("return");

  if (pickup && returnDate) {
    pickup.addEventListener("change", () => {
      if (pickup.value) {
        returnDate.setAttribute("min", pickup.value);

        if (returnDate.value && returnDate.value < pickup.value) {
          returnDate.value = "";
          calculateTotal();
        }
      }
    });
  }
}

function setupBookingType() {
  const bookingType = document.getElementById("bookingType");
  const hourlyFields = document.getElementById("hourlyFields");
  const pickup = document.getElementById("pickup");
  const returnDate = document.getElementById("return");

  if (!bookingType || !hourlyFields || !pickup || !returnDate) {
    return;
  }

  const syncMode = () => {
    const isHourly = bookingType.value === "hour";
    hourlyFields.style.display = isHourly ? "block" : "none";
    if (isHourly) {
      if (pickup.value) {
        returnDate.value = pickup.value;
      }
      returnDate.readOnly = true;
    } else {
      returnDate.readOnly = false;
    }
    calculateTotal();
  };

  bookingType.addEventListener("change", syncMode);
  pickup.addEventListener("change", () => {
    if (bookingType.value === "hour") {
      returnDate.value = pickup.value;
    }
  });

  syncMode();
}

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("activeRole") === "admin") {
    alert("Admin session is active. Logout admin first to book as user.");
    window.location.href = "/admin-login/";
    return;
  }

  attachNavbarActions();
  populateVehicle();
  setMinDateToToday();
  setupDateValidation();
  setupBookingType();

  const pickup = document.getElementById("pickup");
  const returnDate = document.getElementById("return");
  const bookingType = document.getElementById("bookingType");
  const pickupTime = document.getElementById("pickupTime");
  const returnTime = document.getElementById("returnTime");
  const bookBtn = document.querySelector(".booking-box .book-btn");

  pickup?.addEventListener("change", calculateTotal);
  returnDate?.addEventListener("change", calculateTotal);
  bookingType?.addEventListener("change", calculateTotal);
  pickupTime?.addEventListener("change", calculateTotal);
  returnTime?.addEventListener("change", calculateTotal);
  bookBtn?.addEventListener("click", handleBooking);
});

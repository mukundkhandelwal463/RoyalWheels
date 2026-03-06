function ensureCustomerSession() {
  try {
    const activeRole = localStorage.getItem("activeRole");
    const customer = safeJsonParse("loggedCustomer");
    if (activeRole !== "customer" || !customer) {
      alert("Please login as user before booking.");
      window.location.href = "/login.html";
      return false;
    }
    return true;
  } catch (error) {
    alert("Browser storage is blocked or corrupted. Please allow storage and try again.");
    return false;
  }
}

function customerBookingKey(customer) {
  const lpu = String(customer?.lpuId || "").trim().toLowerCase();
  const email = String(customer?.email || "").trim().toLowerCase();
  return lpu || email;
}

function safeJsonParse(storageKey) {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw);
  } catch (error) {
    try {
      localStorage.removeItem(storageKey);
    } catch (_) {}
    alert(`Saved data is corrupted (${storageKey}). Please try again.`);
    return null;
  }
}

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

const hasSession = ensureCustomerSession();
const booking = hasSession ? safeJsonParse("pendingBooking") : null;
const activeCustomer = hasSession ? safeJsonParse("loggedCustomer") : null;
const existingServerBookingId = hasSession ? localStorage.getItem("pendingBookingServerId") : null;

if (hasSession && !booking) {
  const origin = `${window.location.protocol}//${window.location.host}`;
  alert(
    `No booking found.\n\n` +
      `This usually happens when you open payment directly, or you opened it on a different port (example: 7000 vs 8000).\n\n` +
      `Please go to Book Now again and continue to payment on the SAME site/port.\n\n` +
      `Current: ${origin}`
  );
  localStorage.removeItem("pendingBookingServerId");
  window.location.href = "/Car.html";
}

if (hasSession && booking) {
  document.getElementById("vehicleName").innerText = booking.vehicle || "";
  const isHourly = booking.rentalUnit === "hour";
  document.getElementById("pickup").innerText = isHourly
    ? `${booking.pickup || ""} ${booking.pickupTime || ""}`.trim()
    : booking.pickup || "";
  document.getElementById("return").innerText = isHourly
    ? `${booking.returnDate || ""} ${booking.returnTime || ""}`.trim()
    : booking.returnDate || "";

  let computedTotal = booking.total || 0;
  if (isHourly) {
    const start = booking.pickup && booking.pickupTime ? new Date(`${booking.pickup}T${booking.pickupTime}`) : null;
    const end = booking.returnDate && booking.returnTime ? new Date(`${booking.returnDate}T${booking.returnTime}`) : null;
    const hours = start && end ? (end - start) / (1000 * 60 * 60) : 0;
    const billedHours = hours > 0 ? Math.ceil(hours) : 0;
    if (billedHours && booking.pricePerHour) {
      computedTotal = billedHours * Number(booking.pricePerHour);
    }
  } else {
    const pickupDate = booking.pickup ? new Date(booking.pickup) : null;
    const returnDate = booking.returnDate ? new Date(booking.returnDate) : null;
    const days = pickupDate && returnDate ? (returnDate - pickupDate) / (1000 * 60 * 60 * 24) : 0;
    const safeDays = days > 0 ? days : 0;
    if (safeDays && booking.pricePerDay) {
      computedTotal = safeDays * Number(booking.pricePerDay);
    }
  }

  booking.total = computedTotal;
  document.getElementById("total").innerText = String(computedTotal);
  document.getElementById("bookingType").innerText = isHourly ? "Hourly" : "Daily";
  const imageEl = document.getElementById("vehicleImage");
  if (imageEl) {
    imageEl.onerror = () => {
      imageEl.src = "/static/assets/logo.jpg";
    };
    imageEl.src = normalizeImageUrl(booking.image) || "/static/assets/logo.jpg";
  }
}

function processPayment() {
  if (!hasSession || !booking) {
    const origin = `${window.location.protocol}//${window.location.host}`;
    alert(
      `Please book a vehicle first, then come to payment.\n\n` +
        `If you already booked, make sure you're using the same site/port where you booked.\n\n` +
        `Current: ${origin}`
    );
    return;
  }

  const method = document.querySelector("input[name='method']:checked");
  if (!method) {
    alert("Select a payment method.");
    return;
  }

  const methodValue = String(method.value || "").trim().toLowerCase();
  const postJson = async (url, payload) => {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const text = await response.text();
    if (!response.ok) {
      const trimmed = String(text || "").trim();
      if (trimmed.startsWith("<")) {
        const titleMatch = trimmed.match(/<title>([^<]+)<\/title>/i);
        const title = titleMatch ? titleMatch[1] : "Server error";
        throw new Error(`${title}. Check server logs and run migrations if needed.`);
      }
      throw new Error(trimmed || "Request failed");
    }
    return text ? JSON.parse(text) : {};
  };

  const cancelServerBooking = async (serverBookingId) => {
    if (!serverBookingId) return;
    try {
      await postJson("/api/bookings/cancel/", {
        booking_id: serverBookingId,
        customer_email: String(activeCustomer?.email || booking.customerEmail || "").trim(),
        customer_lpu_id: String(activeCustomer?.lpuId || booking.customerLpuId || "").trim()
      });
    } catch (_) {
      // Best effort; even if server cancel fails, we still clear local pending server id.
    } finally {
      try {
        localStorage.removeItem("pendingBookingServerId");
      } catch (_) {}
    }
  };

  const saveConfirmedBooking = (serverBookingId, paymentStatus) => {
    const userKey = customerBookingKey(activeCustomer || {});
    const cacheKey = userKey ? `confirmedBookings:${userKey}` : "confirmedBookings";
    const confirmedBookings = JSON.parse(localStorage.getItem(cacheKey) || "[]");
    confirmedBookings.push({
      ...booking,
      id: serverBookingId,
      status: "pending",
      paymentStatus: paymentStatus || "pending"
    });
    localStorage.setItem(cacheKey, JSON.stringify(confirmedBookings));
  };

  (async () => {
    try {
      let serverBookingId = existingServerBookingId ? Number(existingServerBookingId) : null;

      if (!serverBookingId) {
        const created = await postJson("/api/bookings/create/", {
          vehicle_id: booking.vehicleId,
          customer_name: booking.customerName,
          customer_phone: booking.customerPhone,
          customer_email: booking.customerEmail,
          customer_address: booking.customerAddress,
          customer_lpu_id: booking.customerLpuId,
          customer_license_number: booking.customerLicenseNumber,
          customer_age: booking.customerAge,
          driving_license_doc: booking.drivingLicenseDoc,
          student_id_doc: booking.studentIdDoc,
          rental_unit: booking.rentalUnit || "day",
          start_date: booking.pickup,
          end_date: booking.returnDate,
          start_time: booking.pickupTime || "",
          end_time: booking.returnTime || "",
          total_price: booking.total,
          payment_method: methodValue
        });
        serverBookingId = created.id;
        localStorage.setItem("pendingBookingServerId", String(serverBookingId));
      }

      if (methodValue === "cash") {
        saveConfirmedBooking(serverBookingId, "cod");
        localStorage.removeItem("pendingBooking");
        localStorage.removeItem("pendingBookingServerId");
        alert("Booking placed successfully. Pay at pickup. Awaiting admin approval.");
        window.location.href = "/MyBooking.html";
        return;
      }

      if (methodValue !== "upi") {
        throw new Error("Please select UPI or Pay at Pickup.");
      }

      const order = await postJson("/api/payments/razorpay/order/", { booking_id: serverBookingId });
      const keyId = String(order.key_id || "").trim();
      const orderId = String(order.order_id || "").trim();

      if (!keyId || !orderId) {
        await cancelServerBooking(serverBookingId);
        throw new Error("Unable to start Razorpay checkout (missing order/key).");
      }

      if (typeof Razorpay === "undefined") {
        await cancelServerBooking(serverBookingId);
        throw new Error("Razorpay SDK not loaded. Please check your internet connection.");
      }

      const options = {
        key: keyId,
        amount: order.amount,
        currency: order.currency || "INR",
        name: "RoyalWheels",
        description: `Booking #${serverBookingId}`,
        order_id: orderId,
        prefill: {
          name: booking.customerName || "",
          email: booking.customerEmail || "",
          contact: booking.customerPhone || ""
        },
        handler: async function (response) {
          try {
            await postJson("/api/payments/razorpay/verify/", {
              booking_id: serverBookingId,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });

            saveConfirmedBooking(serverBookingId, "paid");
            localStorage.removeItem("pendingBooking");
            localStorage.removeItem("pendingBookingServerId");
            alert("Payment successful. Booking placed. Awaiting admin approval.");
            window.location.href = "/MyBooking.html";
          } catch (error) {
            alert(`Payment succeeded but verification failed: ${error.message}`);
          }
        },
        modal: {
          ondismiss: function () {
            cancelServerBooking(serverBookingId);
            alert("Payment cancelled.");
          }
        },
        theme: { color: "#2b6cb0" }
      };

      const razorpay = new Razorpay(options);
      razorpay.on("payment.failed", function (response) {
        const message = response?.error?.description || "Payment failed. Please try again.";
        cancelServerBooking(serverBookingId);
        alert(message);
      });
      razorpay.open();
    } catch (error) {
      // If UPI booking was created but checkout couldn't start, cancel it so it won't appear in My Bookings.
      try {
        const methodValue = String(method?.value || "").trim().toLowerCase();
        const serverBookingId = existingServerBookingId ? Number(existingServerBookingId) : Number(localStorage.getItem("pendingBookingServerId") || "0");
        if (methodValue === "upi" && serverBookingId) {
          await cancelServerBooking(serverBookingId);
        }
      } catch (_) {}
      alert(`Unable to place booking/payment: ${error.message}`);
    }
  })();
}

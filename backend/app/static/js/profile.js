const defaultAvatar = "../assets/Mountain.jpg";

function getActiveUser() {
  return JSON.parse(localStorage.getItem("loggedCustomer") || localStorage.getItem("customer") || "null");
}

function saveActiveUser(user) {
  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const normalizedEmail = String(user?.email || "").trim().toLowerCase();
  const normalizedLpu = String(user?.lpuId || "").trim().toLowerCase();
  const index = customers.findIndex((customer) => {
    const email = String(customer?.email || "").trim().toLowerCase();
    const lpu = String(customer?.lpuId || "").trim().toLowerCase();
    return (normalizedEmail && email === normalizedEmail) || (normalizedLpu && lpu === normalizedLpu);
  });

  if (index >= 0) {
    customers[index] = user;
  } else {
    customers.push(user);
  }

  localStorage.setItem("customers", JSON.stringify(customers));
  localStorage.setItem("customer", JSON.stringify(user));
  localStorage.setItem("loggedCustomer", JSON.stringify(user));
}

function customerBookingKey(customer) {
  const lpu = String(customer?.lpuId || "").trim().toLowerCase();
  const email = String(customer?.email || "").trim().toLowerCase();
  return lpu || email;
}

function loadStats() {
  const user = getActiveUser();
  const key = customerBookingKey(user || {});
  const bookings = JSON.parse(localStorage.getItem(key ? `confirmedBookings:${key}` : "confirmedBookings") || "[]");
  let carCount = 0;
  let bikeCount = 0;

  bookings.forEach((booking) => {
    if ((booking.type || "").toLowerCase() === "bike") {
      bikeCount += 1;
    } else {
      carCount += 1;
    }
  });

  document.getElementById("carBookingsCount").textContent = String(carCount);
  document.getElementById("bikeBookingsCount").textContent = String(bikeCount);
}

function loadProfile() {
  const user = getActiveUser();
  if (!user) {
    alert("Please login first.");
    window.location.href = "login.html";
    return;
  }

  document.getElementById("profileName").textContent = user.name || "Guest User";
  document.getElementById("profileEmail").textContent = user.email || "";
  document.getElementById("name").value = user.name || "";
  document.getElementById("email").value = user.email || "";
  document.getElementById("phone").value = user.phone || "";
  document.getElementById("age").value = user.age || "";
  document.getElementById("address").value = user.address || "";
  document.getElementById("lpuId").value = user.lpuId || "";
  document.getElementById("license").value = user.license || "";
  document.getElementById("profileImage").src = user.profilePhoto || defaultAvatar;
}

function setupProfileUpdate() {
  const form = document.getElementById("profileForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const user = getActiveUser();
    if (!user) {
      return;
    }

    const currentEmail = String(user.email || "").trim();
    const newEmail = String(document.getElementById("email").value || "").trim();
    const ageValue = String(document.getElementById("age").value || "").trim();

    if (ageValue) {
      const numericAge = Number(ageValue);
      if (!Number.isInteger(numericAge) || numericAge < 18) {
        alert("Age must be 18 or above.");
        return;
      }
    }

    user.name = document.getElementById("name").value.trim();
    user.email = newEmail;
    user.phone = document.getElementById("phone").value.trim();
    user.age = document.getElementById("age").value.trim();
    user.address = document.getElementById("address").value.trim();
    user.lpuId = document.getElementById("lpuId").value.trim();
    user.license = document.getElementById("license").value.trim();

    const postJson = async (url, payload) => {
      const response = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const text = await response.text();
      if (!response.ok) {
        throw new Error(text || "Request failed");
      }
      return text ? JSON.parse(text) : {};
    };

    try {
      if (newEmail.toLowerCase() !== currentEmail.toLowerCase()) {
        await postJson("/api/customers/profile/update-email/", {
          current_email: currentEmail,
          new_email: newEmail
        });
      }

      await postJson("/api/customers/profile/upsert/", {
        name: user.name,
        email: user.email,
        phone: user.phone,
        age: user.age,
        address: user.address,
        lpu_id: user.lpuId,
        license_number: user.license,
        driving_license_doc: user.drivingLicenseDoc || "",
        student_id_doc: user.studentIdDoc || ""
      });
    } catch (error) {
      alert(error.message || "Unable to save profile to server.");
      return;
    }

    saveActiveUser(user);
    document.getElementById("profileName").textContent = user.name || "Guest User";
    document.getElementById("profileEmail").textContent = user.email || "";
    alert("Profile updated successfully.");
  });
}

function setupPasswordUpdate() {
  const form = document.getElementById("passwordForm");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const user = getActiveUser();
    if (!user) {
      return;
    }

    const current = document.getElementById("currentPassword").value;
    const next = document.getElementById("newPassword").value;
    const confirm = document.getElementById("confirmPassword").value;

    if (current !== user.password) {
      alert("Current password is incorrect.");
      return;
    }

    if (next.length < 6) {
      alert("New password must be at least 6 characters.");
      return;
    }

    if (next !== confirm) {
      alert("New password and confirm password do not match.");
      return;
    }

    user.password = next;
    saveActiveUser(user);
    form.reset();
    alert("Password updated successfully.");
  });
}

function setupPhotoUpload() {
  const photoInput = document.getElementById("profilePhotoInput");
  photoInput.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const user = getActiveUser();
      if (!user) {
        return;
      }

      user.profilePhoto = result;
      saveActiveUser(user);
      document.getElementById("profileImage").src = result;
      alert("Profile photo updated.");
    };
    reader.readAsDataURL(file);
  });
}

function setupDocumentUpload() {
  const form = document.getElementById("documentsForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const user = getActiveUser();
    if (!user) {
      alert("Please login first.");
      window.location.href = "/login.html";
      return;
    }

    const licenseFile = document.getElementById("licenseDoc").files?.[0];
    const collegeFile = document.getElementById("collegeDoc").files?.[0];

    if (!licenseFile || !collegeFile) {
      alert("Please select both Driving License and College ID Card.");
      return;
    }

    const toDataUrl = (file) =>
      new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(new Error("File read failed."));
        reader.readAsDataURL(file);
      });

    try {
      user.drivingLicenseDoc = await toDataUrl(licenseFile);
      user.studentIdDoc = await toDataUrl(collegeFile);
      user.drivingLicenseDocName = licenseFile.name;
      user.studentIdDocName = collegeFile.name;
      saveActiveUser(user);

      const response = await fetch("/api/customers/profile/upsert/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: String(user.name || "").trim(),
          email: String(user.email || "").trim(),
          phone: String(user.phone || "").trim(),
          age: String(user.age || "").trim(),
          address: String(user.address || "").trim(),
          lpu_id: String(user.lpuId || "").trim(),
          license_number: String(user.license || "").trim(),
          driving_license_doc: user.drivingLicenseDoc,
          student_id_doc: user.studentIdDoc
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Server upload failed");
      }

      alert("Documents uploaded successfully.");
    } catch (error) {
      alert(error.message || "Unable to upload documents. Please try again.");
    }
  });
}

function setupLogout() {
  document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("loggedCustomer");
    localStorage.removeItem("activeRole");
    localStorage.removeItem("pendingBooking");
    localStorage.removeItem("selectedVehicle");
    window.location.href = "login.html";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  loadStats();
  setupProfileUpdate();
  setupPasswordUpdate();
  setupPhotoUpload();
  setupDocumentUpload();
  setupLogout();
});

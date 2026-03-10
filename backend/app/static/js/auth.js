async function postJson(url, payload) {
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
}

function normalizeIndianPhone(rawValue) {
  const digits = String(rawValue || "").replace(/\D/g, "");
  let localDigits = digits;

  if (localDigits.startsWith("91") && localDigits.length > 10) {
    localDigits = localDigits.slice(2);
  }

  return localDigits.slice(-10);
}

function enforceIndianPhonePrefix(inputId) {
  const input = document.getElementById(inputId);
  if (!input) {
    return;
  }

  const applyValue = () => {
    input.value = normalizeIndianPhone(input.value);
  };

  input.addEventListener("input", applyValue);
  if (input.value) {
    applyValue();
  }
}

function signup() {
  if (localStorage.getItem("activeRole") === "admin") {
    alert("Admin is currently logged in. Logout from admin first.");
    window.location.href = "/admin-login/";
    return;
  }

  const name = document.getElementById("name")?.value?.trim();
  const email = document.getElementById("email")?.value?.trim();
  const phone = normalizeIndianPhone(document.getElementById("phone")?.value?.trim());
  const age = document.getElementById("age")?.value?.trim();
  const address = document.getElementById("address")?.value?.trim();
  const license = document.getElementById("license")?.value?.trim();
  const lpuId = document.getElementById("lpuId")?.value?.trim();
  const password = document.getElementById("password")?.value;

  if (!name) {
    alert("Please enter your full name");
    return;
  }

  if (!email) {
    alert("Please enter your email address");
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    alert("Please enter a valid email address");
    return;
  }

  if (!password || password.length < 6) {
    alert("Please enter a password (minimum 6 characters)");
    return;
  }

  if (age) {
    const numericAge = Number(age);
    if (!Number.isInteger(numericAge) || numericAge < 18) {
      alert("Age must be 18 or above.");
      return;
    }
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
  }

  const alreadyExists = customers.some(
    (c) =>
      String(c.email || "").toLowerCase() === email.toLowerCase() ||
      (lpuId && String(c.lpuId || "").toLowerCase() === lpuId.toLowerCase())
  );
  if (alreadyExists) {
    alert("An account with this email or LPU ID already exists. Please login instead.");
    return;
  }

  const user = {
    name,
    email,
    phone: phone || "",
    age: age || "",
    address: address || "",
    license: license || "",
    lpuId: lpuId || "",
    password,
    profilePhoto: ""
  };

  try {
    customers.push(user);
    localStorage.setItem("customers", JSON.stringify(customers));
    localStorage.setItem("customer", JSON.stringify(user));
    alert("Signup successful! Please login.");
    window.location.href = "login.html";
  } catch (error) {
    alert("Error saving account. Please try again.");
    console.error("Signup error:", error);
  }
}

function login() {
  if (localStorage.getItem("activeRole") === "admin") {
    alert("Admin is currently logged in. Logout from admin first.");
    window.location.href = "/admin-login/";
    return;
  }

  const email = document.getElementById("loginEmail")?.value?.trim();
  const password = document.getElementById("loginPassword")?.value;

  if (!email) {
    alert("Please enter your email or LPU ID");
    return;
  }

  if (!password) {
    alert("Please enter your password");
    return;
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
    localStorage.setItem("customers", JSON.stringify(customers));
  }

  if (customers.length === 0) {
    alert("No account found. Please signup first.");
    return;
  }

  const normalizedInput = String(email).toLowerCase();
  const matchedUser = customers.find(
    (customer) =>
      (String(customer.email || "").toLowerCase() === normalizedInput ||
        String(customer.lpuId || "").toLowerCase() === normalizedInput) &&
      password === customer.password
  );

  if (matchedUser) {
    localStorage.setItem("loggedCustomer", JSON.stringify(matchedUser));
    localStorage.setItem("activeRole", "customer");
    alert("Login successful!");
    window.location.href = "Home_index.html";
  } else {
    alert("Invalid email/ID or password. Please try again.");
  }
}

function resetCustomerPassword() {
  if (localStorage.getItem("activeRole") === "admin") {
    alert("Admin is currently logged in. Logout from admin first.");
    window.location.href = "/admin-login/";
    return;
  }

  const email = document.getElementById("resetEmail")?.value?.trim();
  const password = document.getElementById("resetPassword")?.value;
  const confirmPassword = document.getElementById("resetConfirmPassword")?.value;

  if (!email) {
    alert("Please enter email.");
    return;
  }

  if (!password || password.length < 6) {
    alert("New password must be at least 6 characters.");
    return;
  }

  if (password !== confirmPassword) {
    alert("New password and confirm password do not match.");
    return;
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
  }

  const normalizedEmail = String(email).toLowerCase();
  const userIndex = customers.findIndex(
    (customer) => String(customer.email || "").toLowerCase() === normalizedEmail
  );

  if (userIndex === -1) {
    alert("Invalid user. Please create an account first.");
    return;
  }

  customers[userIndex].password = password;
  localStorage.setItem("customers", JSON.stringify(customers));
  localStorage.setItem("customer", JSON.stringify(customers[userIndex]));

  const loggedCustomer = JSON.parse(localStorage.getItem("loggedCustomer") || "null");
  if (loggedCustomer && String(loggedCustomer.email || "").toLowerCase() === normalizedEmail) {
    loggedCustomer.password = password;
    localStorage.setItem("loggedCustomer", JSON.stringify(loggedCustomer));
  }

  alert("Password updated successfully. Please login.");
  window.location.href = "/login.html";
}

document.addEventListener("DOMContentLoaded", () => {
  enforceIndianPhonePrefix("phone");
});

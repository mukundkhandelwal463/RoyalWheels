const otpState = {
  customerSignup: {
    email: { otpId: "", target: "", verified: false },
    phone: { otpId: "", target: "", verified: false }
  },
  customerForgot: {
    email: { otpId: "", target: "", verified: false }
  },
  customerProfileEmail: {
    email: { otpId: "", target: "", verified: false }
  },
  customerProfileUpdate: {
    email: { otpId: "", target: "", verified: false }
  },
  customerProfilePassword: {
    email: { otpId: "", target: "", verified: false }
  }
};

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

function resetOtpFlowState(flow, channel) {
  otpState[flow][channel] = { otpId: "", target: "", verified: false };
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

  if (input.value) {
    applyValue();
  }

  input.addEventListener("focus", () => {
    if (!input.value) {
      input.value = "";
    }
  });
  input.addEventListener("input", applyValue);
}

async function sendOtp(flow, channel, target, purpose) {
  if (!target) {
    alert(`Please enter ${channel} first.`);
    return;
  }

  const data = await postJson("/api/otp/send/", {
    purpose,
    channel,
    target
  });

  otpState[flow][channel] = {
    otpId: String(data.otp_id || ""),
    target: String(target).trim(),
    verified: false
  };

  alert(data.message || "OTP sent successfully.");
}

async function verifyOtp(flow, channel, target, code) {
  const state = otpState[flow][channel];
  if (!state.otpId || !state.target) {
    alert(`Please send ${channel} OTP first.`);
    return;
  }
  if (String(state.target).trim() !== String(target).trim()) {
    alert(`${channel} value changed. Please resend OTP.`);
    resetOtpFlowState(flow, channel);
    return;
  }
  if (!code) {
    alert(`Please enter ${channel} OTP.`);
    return;
  }

  await postJson("/api/otp/verify/", {
    otp_id: state.otpId,
    otp_code: String(code).trim()
  });

  otpState[flow][channel].verified = true;
  alert(`${channel.toUpperCase()} OTP verified.`);
}

async function signup() {
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

  if (
    !otpState.customerSignup.email.verified ||
    String(otpState.customerSignup.email.target).trim().toLowerCase() !== String(email).toLowerCase()
  ) {
    alert("Please verify your email OTP before signup.");
    return;
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
    const response = await postJson("/api/customers/signup/", user);
    alert(response.message || "Signup successful! Please login.");
    window.location.href = "login.html";
  } catch (error) {
    alert(error.message || "Error saving account. Please try again.");
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

  const normalizedInput = String(email).toLowerCase();
  
  postJson("/api/customers/login/", {
    email: normalizedInput,
    password: password
  }).then(response => {
    if (response.success && response.user) {
      localStorage.setItem("loggedCustomer", JSON.stringify(response.user));
      localStorage.setItem("activeRole", "customer");
      alert("Login successful!");
      window.location.href = "Home_index.html";
    } else {
      alert("Invalid email/ID or password. Please try again.");
    }
  }).catch(error => {
    alert(error.message || "Invalid email/ID or password. Please try again.");
  });
}

function decodeJwtPayload(token) {
  if (!token || token.split(".").length < 2) {
    return null;
  }

  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(base64)
        .split("")
        .map((char) => `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`)
        .join("")
    );
    return JSON.parse(json);
  } catch (error) {
    console.error("Unable to decode Google credential", error);
    return null;
  }
}

function upsertGoogleCustomer(googleProfile) {
  const email = String(googleProfile?.email || "").trim().toLowerCase();
  if (!email) {
    throw new Error("Google account email is missing.");
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
  }

  const fullName = String(googleProfile?.name || googleProfile?.given_name || email.split("@")[0] || "").trim();
  const picture = String(googleProfile?.picture || "").trim();
  let matchedUser = customers.find(
    (customer) => String(customer.email || "").toLowerCase() === email
  );

  if (!matchedUser) {
    matchedUser = {
      name: fullName,
      email,
      phone: "",
      age: "",
      address: "",
      license: "",
      lpuId: "",
      password: "",
      profilePhoto: picture
    };
    customers.push(matchedUser);
  } else {
    matchedUser.name = matchedUser.name || fullName;
    if (picture) {
      matchedUser.profilePhoto = picture;
    }
  }

  localStorage.setItem("customers", JSON.stringify(customers));
  localStorage.setItem("customer", JSON.stringify(matchedUser));
  localStorage.setItem("loggedCustomer", JSON.stringify(matchedUser));
  localStorage.setItem("activeRole", "customer");
}

function handleGoogleCredentialResponse(response) {
  if (localStorage.getItem("activeRole") === "admin") {
    alert("Admin is currently logged in. Logout from admin first.");
    window.location.href = "/admin-login/";
    return;
  }

  const payload = decodeJwtPayload(response?.credential);
  if (!payload) {
    alert("Google sign-in failed. Please try again.");
    return;
  }

  try {
    upsertGoogleCustomer(payload);
    alert("Login successful!");
    window.location.href = "Home_index.html";
  } catch (error) {
    alert(error.message || "Google login failed.");
  }
}

function initializeGoogleSignIn() {
  const googleClientId = String(window.ROYALWHEELS_GOOGLE_CLIENT_ID || "").trim();
  const buttonContainer = document.getElementById("googleSignInButton");

  if (!googleClientId || !buttonContainer || !window.google?.accounts?.id) {
    return;
  }

  if (buttonContainer.dataset.initialized === "true") {
    return;
  }

  google.accounts.id.initialize({
    client_id: googleClientId,
    callback: handleGoogleCredentialResponse,
    auto_select: false,
    cancel_on_tap_outside: true
  });

  google.accounts.id.renderButton(buttonContainer, {
    theme: "outline",
    size: "large",
    shape: "rectangular",
    text: "continue_with",
    width: 360
  });

  buttonContainer.dataset.initialized = "true";
}

window.initializeGoogleSignIn = initializeGoogleSignIn;

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

  if (
    !otpState.customerForgot.email.verified ||
    String(otpState.customerForgot.email.target).trim().toLowerCase() !== String(email).toLowerCase()
  ) {
    alert("Please verify reset email OTP first.");
    return;
  }

  const normalizedEmail = String(email).toLowerCase();

  postJson("/api/customers/reset-password/", {
    email: normalizedEmail,
    password: password
  }).then(response => {
    alert("Password updated successfully. Please login.");
    resetOtpFlowState("customerForgot", "email");
    window.location.href = "/login.html";
  }).catch(error => {
    alert(error.message || "Unable to reset password.");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initializeGoogleSignIn();
  enforceIndianPhonePrefix("phone");

  document.getElementById("sendEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      await sendOtp(
        "customerSignup",
        "email",
        document.getElementById("email")?.value?.trim(),
        "customer_signup"
      );
    } catch (error) {
      alert(error.message || "Unable to send email OTP.");
    }
  });

  document.getElementById("verifyEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      await verifyOtp(
        "customerSignup",
        "email",
        document.getElementById("email")?.value?.trim(),
        document.getElementById("emailOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify email OTP.");
    }
  });

  document.getElementById("sendResetEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      await sendOtp(
        "customerForgot",
        "email",
        document.getElementById("resetEmail")?.value?.trim(),
        "customer_forgot"
      );
    } catch (error) {
      alert(error.message || "Unable to send reset email OTP.");
    }
  });

  document.getElementById("verifyResetEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      await verifyOtp(
        "customerForgot",
        "email",
        document.getElementById("resetEmail")?.value?.trim(),
        document.getElementById("resetEmailOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify reset email OTP.");
    }
  });

  document.getElementById("sendProfileEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const sendBtn = document.getElementById("sendProfileEmailOtpBtn");
      const otpFlow = sendBtn?.dataset?.otpFlow || "customerProfileEmail";
      const otpPurpose = sendBtn?.dataset?.otpPurpose || "customer_profile_email";
      const otpTarget = sendBtn?.dataset?.otpTarget || document.getElementById("email")?.value?.trim();

      await sendOtp(otpFlow, "email", otpTarget, otpPurpose);
    } catch (error) {
      alert(error.message || "Unable to send profile email OTP.");
    }
  });

  document.getElementById("verifyProfileEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const verifyBtn = document.getElementById("verifyProfileEmailOtpBtn");
      const otpFlow = verifyBtn?.dataset?.otpFlow || "customerProfileEmail";
      const otpTarget = verifyBtn?.dataset?.otpTarget || document.getElementById("email")?.value?.trim();

      await verifyOtp(
        otpFlow,
        "email",
        otpTarget,
        document.getElementById("profileEmailOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify profile email OTP.");
    }
  });

  document.getElementById("sendProfilePasswordEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const userEmail =
        document.getElementById("email")?.value?.trim() ||
        (() => {
          try {
            return JSON.parse(localStorage.getItem("loggedCustomer") || "null")?.email || "";
          } catch (_) {
            return "";
          }
        })();

      await sendOtp("customerProfilePassword", "email", userEmail, "customer_password_change");
    } catch (error) {
      alert(error.message || "Unable to send password change email OTP.");
    }
  });

  document.getElementById("verifyProfilePasswordEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const userEmail =
        document.getElementById("email")?.value?.trim() ||
        (() => {
          try {
            return JSON.parse(localStorage.getItem("loggedCustomer") || "null")?.email || "";
          } catch (_) {
            return "";
          }
        })();

      await verifyOtp(
        "customerProfilePassword",
        "email",
        userEmail,
        document.getElementById("passwordEmailOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify password change email OTP.");
    }
  });
});

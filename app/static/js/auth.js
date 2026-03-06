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
  customerProfileDocs: {
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

  // Keep only last 10 digits
  localDigits = localDigits.slice(-10);

  return localDigits;   // ✅ FIXED (removed curly braces)
}

function enforceIndianPhonePrefix(inputId) {
  const input = document.getElementById(inputId);
  if (!input) {
    return;
  }

  const applyValue = () => {
    input.value = normalizeIndianPhone(input.value);
  };

  if (!input.value) {
    input.value = "";
  } else {
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

  if (data.debug_otp) {
    // Don't show dev OTP to users in popups; log it for developers instead.
    console.info(`[DEV OTP] ${purpose}/${channel} -> ${target}: ${data.debug_otp}`);
  }
  alert("OTP sent successfully.");
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

function parseJwtPayload(jwt) {
  const token = String(jwt || "");
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new Error("Invalid token");
  }
  const base64Url = parts[1];
  const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
  const json = decodeURIComponent(
    atob(padded)
      .split("")
      .map((c) => `%${("00" + c.charCodeAt(0).toString(16)).slice(-2)}`)
      .join("")
  );
  return JSON.parse(json);
}

function ensureCustomerRecordFromGoogle(profile) {
  const email = String(profile?.email || "").trim();
  const name = String(profile?.name || profile?.given_name || "").trim();
  const picture = String(profile?.picture || "").trim();
  const emailVerified = profile?.email_verified;
  if (!email) {
    throw new Error("Google account email is missing.");
  }
  if (emailVerified === false) {
    throw new Error("Your Google email is not verified. Please verify it and try again.");
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
    localStorage.setItem("customers", JSON.stringify(customers));
  }

  const normalizedEmail = email.toLowerCase();
  let existing = customers.find((c) => String(c.email || "").toLowerCase() === normalizedEmail);

  if (!existing) {
    throw new Error("No user found. Please create an account first.");
  }

  // Optional enrichment (do not overwrite user's existing profile).
  let changed = false;
  if (!existing.name && name) {
    existing.name = name;
    changed = true;
  }
  if (picture && !existing.profilePhoto) {
    existing.profilePhoto = picture;
    changed = true;
  }
  if (changed) {
    localStorage.setItem("customers", JSON.stringify(customers));
  }

  localStorage.setItem("loggedCustomer", JSON.stringify(existing));
  localStorage.setItem("activeRole", "customer");
}

function initGoogleLogin() {
  const clientId = String(window.__GOOGLE_CLIENT_ID__ || "").trim();
  const target = document.getElementById("googleSignInBtn");
  if (!clientId || !target) {
    return;
  }

  const tryInit = () => {
    if (!window.google || !google.accounts || !google.accounts.id) {
      return false;
    }

    google.accounts.id.initialize({
      client_id: clientId,
      ux_mode: "popup",
      // Helps when third-party cookies are blocked (Chrome rolling out 3PC deprecation).
      // Uses FedCM where available.
      use_fedcm_for_prompt: true,
      callback: (response) => {
        try {
          if (localStorage.getItem("activeRole") === "admin") {
            alert("Admin is currently logged in. Logout from admin first.");
            window.location.href = "/admin-login/";
            return;
          }
          if (!response || !response.credential) {
            throw new Error("Google sign-in failed.");
          }
          const payload = parseJwtPayload(response.credential);
          ensureCustomerRecordFromGoogle(payload);
          alert("Login successful!");
          window.location.href = "Home_index.html";
        } catch (error) {
          alert(error.message || "Unable to login with Google.");
        }
      }
    });

    google.accounts.id.renderButton(target, {
      theme: "outline",
      size: "large",
      width: 320,
      text: "continue_with"
    });

    // Optional: surfaces One Tap; also useful to see suppression reasons in DevTools.
    try {
      google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed && notification.isNotDisplayed()) {
          console.info("[Google One Tap] not displayed:", notification.getNotDisplayedReason());
        } else if (notification.isSkippedMoment && notification.isSkippedMoment()) {
          console.info("[Google One Tap] skipped:", notification.getSkippedReason());
        } else if (notification.isDismissedMoment && notification.isDismissedMoment()) {
          console.info("[Google One Tap] dismissed:", notification.getDismissedReason());
        }
      });
    } catch (_) {}

    return true;
  };

  if (tryInit()) {
    return;
  }

  // The GSI script can load after DOMContentLoaded; retry a few times.
  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (tryInit() || attempts >= 20) {
      clearInterval(timer);
    }
  }, 250);
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

  if (
    !otpState.customerForgot.email.verified ||
    String(otpState.customerForgot.email.target).trim().toLowerCase() !== String(email).toLowerCase()
  ) {
    alert("Please verify reset email OTP first.");
    return;
  }

  const customers = JSON.parse(localStorage.getItem("customers") || "[]");
  const legacyCustomer = JSON.parse(localStorage.getItem("customer") || "null");
  if (legacyCustomer && !customers.some((c) => c.email === legacyCustomer.email)) {
    customers.push(legacyCustomer);
  }

  const normalizedEmail = String(email).toLowerCase();
  const userIndex = customers.findIndex(
    (customer) =>
      String(customer.email || "").toLowerCase() === normalizedEmail
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
  resetOtpFlowState("customerForgot", "email");
  window.location.href = "/login.html";
}

document.addEventListener("DOMContentLoaded", () => {
  enforceIndianPhonePrefix("phone");
  initGoogleLogin();

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

  document.getElementById("sendPhoneOtpBtn")?.addEventListener("click", async () => {
    try {
      await sendOtp(
        "customerSignup",
        "phone",
        normalizeIndianPhone(document.getElementById("phone")?.value?.trim()),
        "customer_signup"
      );
    } catch (error) {
      alert(error.message || "Unable to send phone OTP.");
    }
  });

  document.getElementById("verifyPhoneOtpBtn")?.addEventListener("click", async () => {
    try {
      await verifyOtp(
        "customerSignup",
        "phone",
        normalizeIndianPhone(document.getElementById("phone")?.value?.trim()),
        document.getElementById("phoneOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify phone OTP.");
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

  // Profile email OTP
  document.getElementById("sendProfileEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const sendBtn = document.getElementById("sendProfileEmailOtpBtn");
      const otpFlow = sendBtn?.dataset?.otpFlow || "customerProfileEmail";
      const otpPurpose = sendBtn?.dataset?.otpPurpose || "customer_profile_email";
      const otpTarget =
        sendBtn?.dataset?.otpTarget ||
        document.getElementById("email")?.value?.trim();

      await sendOtp(
        otpFlow,
        "email",
        otpTarget,
        otpPurpose
      );
    } catch (error) {
      alert(error.message || "Unable to send profile email OTP.");
    }
  });

  document.getElementById("verifyProfileEmailOtpBtn")?.addEventListener("click", async () => {
    try {
      const verifyBtn = document.getElementById("verifyProfileEmailOtpBtn");
      const otpFlow = verifyBtn?.dataset?.otpFlow || "customerProfileEmail";
      const otpTarget =
        verifyBtn?.dataset?.otpTarget ||
        document.getElementById("email")?.value?.trim();

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

  // Profile documents email OTP (required before uploading docs)
  document.getElementById("sendProfileDocsEmailOtpBtn")?.addEventListener("click", async () => {
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
      await sendOtp(
        "customerProfileDocs",
        "email",
        userEmail,
        "customer_profile_docs"
      );
    } catch (error) {
      alert(error.message || "Unable to send documents email OTP.");
    }
  });

  document.getElementById("verifyProfileDocsEmailOtpBtn")?.addEventListener("click", async () => {
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
        "customerProfileDocs",
        "email",
        userEmail,
        document.getElementById("docsEmailOtp")?.value?.trim()
      );
    } catch (error) {
      alert(error.message || "Unable to verify documents email OTP.");
    }
  });

  // Change password email OTP (required before password update)
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
      await sendOtp(
        "customerProfilePassword",
        "email",
        userEmail,
        "customer_password_change"
      );
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

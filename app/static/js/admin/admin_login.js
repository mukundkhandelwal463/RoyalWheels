function signup() {
  const admin = {
    shop: document.getElementById("shop")?.value?.trim(),
    owner: document.getElementById("owner")?.value?.trim(),
    email: document.getElementById("email")?.value?.trim(),
    phone: document.getElementById("phone")?.value?.trim(),
    address: document.getElementById("address")?.value?.trim(),
    gst: document.getElementById("gst")?.value?.trim(),
    password: document.getElementById("password")?.value,
    role: "admin"
  };

  if (!admin.email || !admin.password || !admin.shop || !admin.owner) {
    alert("Please fill all required fields.");
    return;
  }

  localStorage.setItem("admin_" + admin.email, JSON.stringify(admin));
  alert("Admin registered successfully.");
  window.location.href = "admin_login.html";
}

function login() {
  const email = document.getElementById("loginEmail")?.value?.trim();
  const password = document.getElementById("loginPassword")?.value;

  if (!email || !password) {
    alert("Please enter email and password.");
    return;
  }

  const admin = JSON.parse(localStorage.getItem("admin_" + email));

  if (!admin || admin.password !== password) {
    alert("Invalid admin credentials.");
    return;
  }

  localStorage.setItem("loggedAdmin", JSON.stringify(admin));
  alert("Welcome Admin.");
  window.location.href = "../Home_index.html";
}

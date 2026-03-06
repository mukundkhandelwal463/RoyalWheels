function parsePrice(card) {
  const priceText = card.querySelector(".car-price")?.textContent || "0";
  const normalized = priceText.replace(/,/g, "");
  const match = normalized.match(/(\d+(\.\d+)?)/);
  return match ? Number(match[1]) : 0;
}

function ensureCanBook() {
  const activeRole = localStorage.getItem("activeRole");
  if (!activeRole) {
    alert("Please login first to book a vehicle.");
    window.location.href = "/login.html";
    return false;
  }
  if (activeRole === "admin") {
    alert("Admin account cannot create customer bookings. Please login as user.");
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

function getVehicleFromCard(card) {
  const vehicleId = Number(card.getAttribute("data-vehicle-id") || "0");
  const vehicle = card.querySelector(".car-name")?.textContent?.trim() || "Vehicle";
  const image = card.querySelector(".car-img")?.getAttribute("src") || "../assets/logo.jpg";
  const pricePerDay = parsePrice(card);
  const type = card.getAttribute("data-type") || "Vehicle";
  return { vehicleId, vehicle, image, pricePerDay, type };
}

document.addEventListener("DOMContentLoaded", () => {
  const cards = Array.from(document.querySelectorAll(".search-card"));
  cards.forEach((card) => {
    const button = card.querySelector(".book-btn");
    button?.addEventListener("click", (event) => {
      event.preventDefault();
      if (!ensureCanBook()) return;
      const selectedVehicle = getVehicleFromCard(card);
      localStorage.setItem("selectedVehicle", JSON.stringify(selectedVehicle));
      window.location.href = "/Book_now.html";
    });
  });
});


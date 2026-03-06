function parsePrice(card) {
  const dataPrice = card.getAttribute("data-price") || card.dataset.price;
  if (dataPrice != null && dataPrice !== "") {
    const num = Number(String(dataPrice).replace(/,/g, "").trim());
    if (Number.isFinite(num)) {
      return num;
    }
  }

  const priceText = card.querySelector(".car-price")?.textContent || "0";
  const normalized = priceText.replace(/,/g, "");
  const match = normalized.match(/(\d+(\.\d+)?)/);
  return match ? Number(match[1]) : 0;
}

function parseRating(card) {
  const specs = card.querySelectorAll(".car-specs .spec");
  for (const spec of specs) {
    const text = spec.textContent || "";
    const match = text.match(/([0-5](\.[0-9]+)?)/);
    if (match && text.includes(".")) {
      return Number(match[1]);
    }
  }
  return 0;
}
 
function getVehicleFromCard(card, type) {
  const vehicleId = Number(card.getAttribute("data-vehicle-id") || "0");
  const vehicle = card.querySelector(".car-name")?.textContent?.trim() || "Vehicle";
  const image = card.querySelector(".car-img")?.getAttribute("src") || "../assets/BMW.png";
  const pricePerDay = parsePrice(card);
  return { vehicleId, vehicle, image, pricePerDay, type };
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

function normalizeText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function getSortSelect() {
  return (
    document.getElementById("carSort") ||
    document.getElementById("sortSelect") ||
    document.getElementById("vehicleSort")
  );
}

function getCardSearchText(card) {
  const brand = normalizeText(card.getAttribute("data-brand") || card.dataset.brand);
  const nameData = normalizeText(card.getAttribute("data-name") || card.dataset.name);
  const ownerData = normalizeText(card.getAttribute("data-owner") || card.dataset.owner);
  const nameText = normalizeText(card.querySelector(".car-name")?.textContent);
  const subtitleText = normalizeText(card.querySelector(".car-subtitle")?.textContent);
  return normalizeText(`${brand} ${nameData} ${ownerData} ${nameText} ${subtitleText}`);
}

function getCardName(card) {
  const nameData = normalizeText(card.getAttribute("data-name") || card.dataset.name);
  if (nameData) {
    return nameData;
  }
  return normalizeText(card.querySelector(".car-name")?.textContent);
}

function attachFilterAndSort(cards) {
  const parent =
    document.getElementById("carsContainer") || document.querySelector(".cars-row");
  if (!parent) {
    return;
  }

  const searchInput = document.querySelector(".search-bar input");
  const sortSelect = getSortSelect();
  const originalOrder = [...cards];

  function applyFilterAndSort() {
    const q = normalizeText(searchInput?.value);
    const sortValue = String(sortSelect?.value || "");

    cards.forEach((card) => {
      const text = getCardSearchText(card);
      const show = q === "" || text.includes(q);
      card.style.display = show ? "" : "none";
    });

    const visibleCards = originalOrder.filter((card) => card.style.display !== "none");

    const ordered =
      sortValue === "" || visibleCards.length <= 1
        ? visibleCards
        : [...visibleCards].sort((a, b) => {
            if (sortValue === "price-low" || sortValue === "priceLow") {
              return parsePrice(a) - parsePrice(b);
            }
            if (sortValue === "price-high" || sortValue === "priceHigh") {
              return parsePrice(b) - parsePrice(a);
            }
            if (sortValue === "name") {
              return getCardName(a).localeCompare(getCardName(b));
            }
            if (sortValue === "name-desc") {
              return getCardName(b).localeCompare(getCardName(a));
            }
            if (sortValue === "rating") {
              return parseRating(b) - parseRating(a);
            }
            return 0;
          });

    ordered.forEach((card) => parent.appendChild(card));
  }

  searchInput?.addEventListener("input", applyFilterAndSort);
  sortSelect?.addEventListener("change", applyFilterAndSort);
  sortSelect?.addEventListener("input", applyFilterAndSort);

  applyFilterAndSort();
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

document.addEventListener("DOMContentLoaded", () => {
  attachNavbarActions();

  const cards = Array.from(document.querySelectorAll(".cars-row .car-card"));
  if (cards.length === 0) {
    return;
  }

  attachFilterAndSort(cards);

  cards.forEach((card) => {
    const button = card.querySelector(".book-btn");
    button?.addEventListener("click", (event) => {
      event.preventDefault();
      if (!ensureCanBook()) {
        return;
      }
      const selectedVehicle = getVehicleFromCard(card, "Car");
      localStorage.setItem("selectedVehicle", JSON.stringify(selectedVehicle));
      window.location.href = "/Book_now.html";
    });
  });
});

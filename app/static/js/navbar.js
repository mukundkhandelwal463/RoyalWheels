function getNavbarUser() {
  return JSON.parse(localStorage.getItem("loggedCustomer") || "null");
}

function setupNavbarProfileAvatar() {
  const navActions = document.querySelector(".nav-actions");
  if (!navActions) return;

  const user = getNavbarUser();
  const loginBtn = navActions.querySelector(".btn-primary");
  const existingAvatar = navActions.querySelector(".nav-avatar-link");

  if (!user) {
    // User not logged in - show login button, hide avatar
    if (existingAvatar) existingAvatar.remove();
    if (loginBtn) {
      loginBtn.style.display = "";
      loginBtn.style.visibility = "visible";
    }
    return;
  }

  // User is logged in - hide login button, show avatar
  if (loginBtn) {
    loginBtn.style.display = "none";
    loginBtn.style.visibility = "hidden";
  }

  // Create or update avatar link
  let avatarLink = existingAvatar;
  if (!avatarLink) {
    avatarLink = document.createElement("a");
    avatarLink.className = "nav-avatar-link";
    navActions.appendChild(avatarLink);
  }

  avatarLink.href = "profile.html";
  avatarLink.title = user.name || "My Profile";
  avatarLink.setAttribute("aria-label", "Open profile");

  // Create or update avatar image
  let avatarImg = avatarLink.querySelector("img");
  if (!avatarImg) {
    avatarImg = document.createElement("img");
    avatarLink.appendChild(avatarImg);
  }

  avatarImg.className = "nav-avatar";
  avatarImg.alt = user.name || "Profile";
  
  // Use profile photo or default avatar
  const defaultAvatar = "../assets/logo.jpg"; // Using logo as default circular avatar
  avatarImg.src = user.profilePhoto || defaultAvatar;
  
  // Handle image load errors
  avatarImg.onerror = function() {
    this.src = defaultAvatar;
  };
}

// Run on page load
document.addEventListener("DOMContentLoaded", setupNavbarProfileAvatar);

// Also run after a short delay to catch dynamically loaded navbars
setTimeout(setupNavbarProfileAvatar, 100);

// --- Navbar search + animated placeholder ---
function setupNavbarSearch() {
  const searchInput = document.querySelector('.navbar .search-wrapper input');
  if (!searchInput) return;

  // Cleanup: remove any previously injected navbar clear buttons.
  const wrapper = searchInput.closest(".search-wrapper");
  wrapper?.querySelectorAll(".search-clear").forEach((el) => el.remove());

  function getPageScope() {
    if (document.getElementById("carsContainer")) return "cars";
    if (document.getElementById("bikesContainer")) return "bikes";
    if (document.querySelector(".partners-detailed")) return "partners";
    if (document.querySelector(".cars-row .car-card")) return "vehicles";
    return "all";
  }

  function ensureClearButton(wrapper) {
    if (!wrapper || wrapper.querySelector(".search-clear")) return null;
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "search-clear";
    clear.setAttribute("aria-label", "Clear search");
    clear.innerHTML = "×";
    wrapper.appendChild(clear);
    return clear;
  }

  // Typing-placeholder animation
  const scope = getPageScope();
  const phrasesByScope = {
    partners: ["Search partners, cars, bikes", "e.g. Partner name", "e.g. BMW X7", "e.g. Royal Enfield"],
    cars: ["Search cars, bikes, partners", "e.g. BMW X7", "e.g. Partner name", "e.g. Royal Enfield"],
    bikes: ["Search bikes, cars, partners", "e.g. Royal Enfield", "e.g. Partner name", "e.g. BMW X7"],
    vehicles: ["Search vehicles, partners", "e.g. BMW X7", "e.g. Hunter 350", "e.g. Partner name"],
    all: ["Search cars, bikes, partners", "e.g. Partner name", "e.g. BMW X7", "e.g. Royal Enfield"],
  };
  const phrases = phrasesByScope[scope] || phrasesByScope.all;
  let pIndex = 0;
  let charIndex = 0;
  let typing = true;
  let animDelay = 80;
  let loopDelay = 1200;
  let animTimer = null;

  function startAnimation() {
    if (animTimer) clearTimeout(animTimer);
    animTimer = setTimeout(tick, animDelay);
  }

  function tick() {
    const phrase = phrases[pIndex];
    if (typing) {
      charIndex++;
      searchInput.placeholder = phrase.slice(0, charIndex);
      if (charIndex >= phrase.length) {
        typing = false;
        animTimer = setTimeout(tick, loopDelay);
        return;
      }
    } else {
      charIndex--;
      searchInput.placeholder = phrase.slice(0, Math.max(0, charIndex));
      if (charIndex <= 0) {
        typing = true;
        pIndex = (pIndex + 1) % phrases.length;
      }
    }
    animTimer = setTimeout(tick, animDelay);
  }

  // Pause animation when user focuses or types
  function pauseAnimation() {
    if (animTimer) { clearTimeout(animTimer); animTimer = null; }
  }

  function resumeAnimation() {
    if (!animTimer && !searchInput.value) startAnimation();
  }

  searchInput.addEventListener('focus', pauseAnimation);
  searchInput.addEventListener('input', pauseAnimation);
  searchInput.addEventListener('blur', resumeAnimation);

  // Start only if input empty
  if (!searchInput.value) startAnimation();

  function dispatchToPageSearch(value) {
    const normalized = String(value || "");
    const carSearch = document.getElementById("carSearch");
    const bikeSearch = document.getElementById("bikeSearch");

    if (carSearch) {
      carSearch.value = normalized;
      carSearch.dispatchEvent(new Event("input", { bubbles: true }));
    }

    if (bikeSearch) {
      bikeSearch.value = normalized;
      bikeSearch.dispatchEvent(new Event("input", { bubbles: true }));
    }

    const partnersList = document.querySelector(".partners-detailed");
    if (partnersList) {
      const q = normalized.trim().toLowerCase();
      const rows = Array.from(partnersList.querySelectorAll(".partner-row"));
      rows.forEach((row) => {
        const name = row.querySelector("h2")?.textContent?.trim().toLowerCase() || "";
        const rightText = row.querySelector(".partner-right")?.textContent?.trim().toLowerCase() || "";
        const show = q === "" || name.includes(q) || rightText.includes(q);
        row.style.display = show ? "" : "none";
      });
    }
  }

  // Live-filter listing pages while typing (cars/bikes/partners).
  searchInput.addEventListener("input", () => dispatchToPageSearch(searchInput.value));

  // Enter key: global search page (cars + bikes + partners).
  searchInput.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    const q = searchInput.value.trim();
    if (!q) return;
    window.location.href = "/Search.html?q=" + encodeURIComponent(q);
  });

  // If ?q= is present, prefill navbar and filter in-page.
  try {
    const url = new URL(window.location.href);
    const q = url.searchParams.get("q");
    if (q && !searchInput.value) {
      searchInput.value = q;
      pauseAnimation();
      dispatchToPageSearch(q);
    }
  } catch {}
}

document.addEventListener('DOMContentLoaded', setupNavbarSearch);
setTimeout(setupNavbarSearch, 120);

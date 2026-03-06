document.addEventListener("DOMContentLoaded", () => {
    const messages = document.querySelectorAll(".message");
    if (!messages.length) {
        // continue to setup other page interactions
    }

    if (messages.length) {
        setTimeout(() => {
            messages.forEach((item) => {
                item.style.opacity = "0";
                item.style.transition = "opacity 0.3s ease";
            });
        }, 3200);
    }

    const photoInput = document.getElementById("id_profile_photo");
    const preview = document.getElementById("profilePhotoPreview");
    const sidebarPhoto = document.getElementById("sidebarProfilePhoto");

    if (photoInput && preview) {
        photoInput.addEventListener("change", () => {
            const file = photoInput.files && photoInput.files[0];
            if (!file) {
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                preview.src = reader.result;
                if (sidebarPhoto && sidebarPhoto.tagName === "IMG") {
                    sidebarPhoto.src = reader.result;
                }
            };
            reader.readAsDataURL(file);
            if (sidebarPhoto && sidebarPhoto.tagName !== "IMG") {
                const img = document.createElement("img");
                img.id = "sidebarProfilePhoto";
                img.className = "admin-photo";
                img.alt = "Admin Photo";
                img.src = URL.createObjectURL(file);
                sidebarPhoto.replaceWith(img);
            }
        });
    }
});

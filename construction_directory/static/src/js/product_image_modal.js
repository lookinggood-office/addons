/** @odoo-module **/

const photoState = new WeakMap();

function showPhoto(modal, state, index) {
    state.index = (index + state.photos.length) % state.photos.length;
    const photo = state.photos[state.index];
    const image = modal.querySelector(".product-image-modal-preview");
    const counter = modal.querySelector(".product-image-modal-count");
    image.src = photo.dataset.imageSrc || "";
    image.alt = photo.dataset.imageAlt || "รูปสินค้า";
    counter.textContent = `${state.index + 1} / ${state.photos.length}`;
}

document.addEventListener("show.bs.modal", (event) => {
    const modal = event.target;
    if (!modal.matches(".product-image-modal")) {
        return;
    }

    const trigger = event.relatedTarget;
    const gallery = trigger?.closest(".product-detail-gallery");
    const photos = [...(gallery?.querySelectorAll(".product-gallery-image-trigger") || [])];
    if (!trigger || !photos.length) {
        return;
    }

    const state = { photos, index: Number(trigger.dataset.photoIndex || 0) };
    photoState.set(modal, state);
    showPhoto(modal, state, state.index);
    modal.querySelector(".product-image-modal-prev").hidden = photos.length < 2;
    modal.querySelector(".product-image-modal-next").hidden = photos.length < 2;
});

document.addEventListener("slide.bs.carousel", (event) => {
    const carousel = event.target;
    if (!carousel.matches(".product-image-gallery")) {
        return;
    }
    const gallery = carousel.closest(".product-detail-gallery");
    gallery?.querySelectorAll(".product-gallery-thumbnail").forEach((thumbnail) => {
        const active = Number(thumbnail.dataset.bsSlideTo) === event.to;
        thumbnail.classList.toggle("active", active);
        if (active) {
            thumbnail.setAttribute("aria-current", "true");
        } else {
            thumbnail.removeAttribute("aria-current");
        }
    });
});

document.addEventListener("click", (event) => {
    const modal = event.target.closest(".product-image-modal");
    const state = modal && photoState.get(modal);
    if (!state) {
        return;
    }
    if (event.target.closest(".product-image-modal-prev")) {
        showPhoto(modal, state, state.index - 1);
    } else if (event.target.closest(".product-image-modal-next")) {
        showPhoto(modal, state, state.index + 1);
    }
});

document.addEventListener("keydown", (event) => {
    const modal = document.querySelector(".product-image-modal.show");
    const state = modal && photoState.get(modal);
    if (!state || state.photos.length < 2) {
        return;
    }
    if (event.key === "ArrowLeft") {
        showPhoto(modal, state, state.index - 1);
    } else if (event.key === "ArrowRight") {
        showPhoto(modal, state, state.index + 1);
    }
});

document.addEventListener("pointerdown", (event) => {
    const image = event.target.closest(".product-image-modal-preview");
    if (image) {
        image.dataset.swipeStartX = String(event.clientX);
        image.setPointerCapture?.(event.pointerId);
    }
});

document.addEventListener("pointerup", (event) => {
    const image = event.target.closest(".product-image-modal-preview");
    const modal = image?.closest(".product-image-modal");
    const state = modal && photoState.get(modal);
    if (!image || !state || state.photos.length < 2) {
        return;
    }
    const startX = Number(image.dataset.swipeStartX);
    delete image.dataset.swipeStartX;
    const deltaX = event.clientX - startX;
    if (Math.abs(deltaX) > 45) {
        showPhoto(modal, state, state.index + (deltaX < 0 ? 1 : -1));
    }
});

document.addEventListener("hidden.bs.modal", (event) => {
    const modal = event.target;
    if (!modal.matches(".product-image-modal")) {
        return;
    }

    const image = modal.querySelector(".product-image-modal-preview");
    if (image) {
        image.removeAttribute("src");
        image.alt = "";
    }
    modal.querySelector(".product-image-modal-count").textContent = "";
    photoState.delete(modal);
});

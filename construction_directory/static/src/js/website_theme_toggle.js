/** @odoo-module **/

const storageKey = "warehouse-co-website-theme";
const root = document.documentElement;

function readTheme() {
    try {
        return window.localStorage.getItem(storageKey) === "dark" ? "dark" : "light";
    } catch {
        return "light";
    }
}

function applyTheme(theme) {
    const isDark = theme === "dark";
    root.dataset.warehouseTheme = isDark ? "dark" : "light";
    document.querySelectorAll("[data-warehouse-theme-toggle]").forEach((button) => {
        const label = isDark ? "Switch to light mode" : "Switch to dark mode";
        button.setAttribute("aria-label", label);
        button.setAttribute("title", label);
        button.setAttribute("aria-pressed", String(isDark));
        const icon = button.querySelector("i");
        if (icon) {
            icon.classList.toggle("fa-moon-o", !isDark);
            icon.classList.toggle("fa-sun-o", isDark);
        }
        button.querySelectorAll("[data-warehouse-theme-label]").forEach((text) => {
            text.textContent = isDark ? "Light mode" : "Dark mode";
        });
    });
}

applyTheme(readTheme());

function bindThemeToggle() {
    applyTheme(root.dataset.warehouseTheme);
    document.addEventListener("click", (event) => {
        const button = event.target.closest("[data-warehouse-theme-toggle]");
        if (!button) {
            return;
        }
        const theme = root.dataset.warehouseTheme === "dark" ? "light" : "dark";
        applyTheme(theme);
        try {
            window.localStorage.setItem(storageKey, theme);
        } catch {
            // Keep the current page usable when browser storage is disabled.
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindThemeToggle, { once: true });
} else {
    bindThemeToggle();
}

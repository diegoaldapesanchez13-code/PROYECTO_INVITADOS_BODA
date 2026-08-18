(() => {
    "use strict";

    const toastRegion = document.getElementById("app-toast-region");

    function showToast(text, level = "info", timeout = 3800) {
        if (!toastRegion || !text) return;

        const toast = document.createElement("div");
        toast.className = `app-toast app-toast--${level}`;
        toast.setAttribute("role", level === "error" || level === "danger" ? "alert" : "status");
        toast.textContent = text;
        toastRegion.appendChild(toast);

        window.setTimeout(() => {
            toast.remove();
        }, timeout);
    }

    const messagesNode = document.getElementById("app-django-messages");
    if (messagesNode) {
        try {
            JSON.parse(messagesNode.textContent).forEach((message) => {
                showToast(message.text, message.level || "info");
            });
        } catch (_error) {
            // Presentation failure must never break the page.
        }
    }

    const dialog = document.querySelector("[data-app-dialog]");
    const backdrop = document.querySelector("[data-overlay-backdrop]");
    const dialogTitle = document.querySelector("[data-dialog-title]");
    const dialogBody = document.querySelector("[data-dialog-body]");
    let lastFocused = null;

    function closeDialog() {
        if (!dialog || !backdrop) return;
        dialog.hidden = true;
        backdrop.hidden = true;
        document.documentElement.style.overflow = "";
        if (lastFocused && typeof lastFocused.focus === "function") {
            lastFocused.focus();
        }
    }

    function openDialog({ title = "Acción", html = "" } = {}) {
        if (!dialog || !backdrop || !dialogTitle || !dialogBody) return;
        lastFocused = document.activeElement;
        dialogTitle.textContent = title;
        dialogBody.innerHTML = html;
        backdrop.hidden = false;
        dialog.hidden = false;
        document.documentElement.style.overflow = "hidden";
        const firstFocusable = dialog.querySelector("button, a, input, select, textarea, [tabindex]:not([tabindex='-1'])");
        firstFocusable?.focus();
    }

    document.addEventListener("click", (event) => {
        const closeButton = event.target.closest("[data-dialog-close]");
        if (closeButton || event.target === backdrop) {
            closeDialog();
            return;
        }

        const trigger = event.target.closest("[data-dialog-trigger]");
        if (trigger) {
            openDialog({
                title: trigger.dataset.dialogTitle || "Acción",
                html: trigger.dataset.dialogHtml || "",
            });
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && dialog && !dialog.hidden) {
            closeDialog();
        }
    });

    window.DIRTECApp = Object.freeze({
        showToast,
        openDialog,
        closeDialog,
    });
})();

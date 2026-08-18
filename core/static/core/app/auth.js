(() => {
    "use strict";

    document.addEventListener("click", (event) => {
        const toggle = event.target.closest("[data-password-toggle]");
        if (!toggle) return;

        const input = document.getElementById(toggle.dataset.passwordToggle);
        if (!input) return;

        const showing = input.type === "text";
        input.type = showing ? "password" : "text";
        toggle.setAttribute("aria-pressed", showing ? "false" : "true");
        toggle.setAttribute("aria-label", showing ? "Mostrar contraseña" : "Ocultar contraseña");

        const label = toggle.querySelector("[data-password-toggle-text]");
        if (label) {
            label.textContent = showing ? "Mostrar" : "Ocultar";
        }

        input.focus({ preventScroll: true });
    });

    document.addEventListener("submit", (event) => {
        const form = event.target.closest(".auth-form");
        if (!form) return;

        const submit = form.querySelector("[data-auth-submit]");
        if (!submit || submit.disabled) return;

        submit.classList.add("is-loading");
        submit.disabled = true;

        const label = submit.querySelector("[data-submit-label]");
        if (label) {
            label.dataset.originalText = label.textContent;
            label.textContent = "Procesando…";
        }
    });
})();

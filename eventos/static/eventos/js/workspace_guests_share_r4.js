(() => {
  "use strict";

  function absoluteInvitationUrl(container) {
    const path = container?.dataset.invitationPath || "";
    return path ? new URL(path, window.location.origin).href : "";
  }

  function feedback(container, message, error = false) {
    const target = container.querySelector("[data-share-feedback]");
    if (!target) return;
    target.textContent = message;
    target.classList.toggle("is-error", error);
    window.clearTimeout(target._dirtecTimer);
    target._dirtecTimer = window.setTimeout(() => {
      target.textContent = "";
      target.classList.remove("is-error");
    }, 2200);
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const input = document.createElement("textarea");
    input.value = text;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    const ok = document.execCommand("copy");
    input.remove();
    if (!ok) throw new Error("copy-failed");
  }

  function initGuestSharing() {
    document.querySelectorAll("[data-invitation-share]").forEach((container) => {
      if (container.dataset.shareReady === "1") return;
      container.dataset.shareReady = "1";

      container.querySelector("[data-copy-invitation]")?.addEventListener("click", async () => {
        const url = absoluteInvitationUrl(container);
        if (!url) return feedback(container, "No se encontró el enlace.", true);
        try {
          await copyText(url);
          feedback(container, "Enlace copiado");
        } catch (_) {
          feedback(container, "No se pudo copiar.", true);
        }
      });

      container.querySelector("[data-whatsapp-invitation]")?.addEventListener("click", () => {
        const url = absoluteInvitationUrl(container);
        const name = (container.dataset.invitationName || "").trim();
        if (!url) return feedback(container, "No se encontró el enlace.", true);

        const greeting = name ? `Hola ${name}, ` : "Hola, ";
        const message = `${greeting}te comparto tu invitación al evento:\n${url}`;
        const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
        window.open(whatsappUrl, "_blank", "noopener,noreferrer");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGuestSharing, { once: true });
  } else {
    initGuestSharing();
  }

  // Compatible con K9.R4 Global No Refresh Navigation.
  document.addEventListener("dirtec:workspace:loaded", initGuestSharing);
})();
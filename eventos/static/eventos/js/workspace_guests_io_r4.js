(() => {
  "use strict";

  function initGuestIO() {
    const root = document.querySelector("[data-guests-workspace]");
    if (!root || root.dataset.ioReady === "1") return;

    root.dataset.ioReady = "1";
    const dialog = document.querySelector("[data-import-guests-dialog]");
    const openButton = root.querySelector("[data-import-guests-open]");

    openButton?.addEventListener("click", () => {
      if (!dialog) return;
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "");
      }
    });

    dialog?.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const inside =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (!inside) dialog.close?.();
    });

    const fileInput = dialog?.querySelector("input[type='file']");
    fileInput?.addEventListener("change", () => {
      const label = dialog.querySelector(".guest-import-dropzone > span");
      const file = fileInput.files?.[0];
      if (label && file) {
        label.textContent = file.name;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGuestIO, { once: true });
  } else {
    initGuestIO();
  }

  // The dialog is re-bound after partial Workspace navigation.
  document.addEventListener("dirtec:workspace:loaded", initGuestIO);
})();
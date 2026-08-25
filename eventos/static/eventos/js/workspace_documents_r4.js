(() => {
  "use strict";

  function openDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function initDocumentsWorkspace() {
    const root = document.querySelector("[data-documents-workspace]");
    if (!root || root.dataset.documentsReady === "1") return;
    root.dataset.documentsReady = "1";

    const uploadDialog = root.querySelector("[data-document-upload-dialog]");
    root.querySelector("[data-document-upload-open]")?.addEventListener("click", () => {
      openDialog(uploadDialog);
    });

    const archiveDialog = root.querySelector("[data-document-archive-dialog]");
    const archiveForm = archiveDialog?.querySelector("[data-document-archive-form]");
    const archiveCopy = archiveDialog?.querySelector("[data-document-archive-copy]");

    root.querySelectorAll("[data-document-archive-open]").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.documentId;
        const title = button.dataset.documentTitle || "este documento";
        if (!archiveForm || !id) return;

        const current = new URL(window.location.href);
        const base = current.pathname.replace(/\/documentos\/?$/, "/documentos/");
        archiveForm.action = `${base}${id}/archivar/`;

        if (archiveCopy) {
          archiveCopy.textContent =
            `“${title}” dejará de aparecer entre los activos, pero se conservará como historial.`;
        }
        openDialog(archiveDialog);
      });
    });

    const replaceDialog = root.querySelector("[data-document-replace-dialog]");
    const replaceForm = replaceDialog?.querySelector("[data-document-replace-form]");
    const replaceCopy = replaceDialog?.querySelector("[data-document-replace-copy]");

    root.querySelectorAll("[data-document-replace-open]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.documentAction;
        const title = button.dataset.documentTitle || "este documento";
        if (!replaceForm || !action) return;

        replaceForm.action = action;
        replaceForm.reset();

        if (replaceCopy) {
          replaceCopy.textContent =
            `Se reemplazará únicamente el archivo físico de “${title}”. El registro, título, tipo, permisos y relaciones se conservarán.`;
        }
        openDialog(replaceDialog);
      });
    });

    const deleteDialog = root.querySelector("[data-document-delete-dialog]");
    const deleteForm = deleteDialog?.querySelector("[data-document-delete-form]");
    const deleteCopy = deleteDialog?.querySelector("[data-document-delete-copy]");

    root.querySelectorAll("[data-document-delete-open]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.documentAction;
        const title = button.dataset.documentTitle || "este documento";
        if (!deleteForm || !action) return;

        deleteForm.action = action;
        deleteForm.reset();

        if (deleteCopy) {
          deleteCopy.textContent =
            `“${title}” se eliminará permanentemente junto con su archivo físico. Esta acción no se puede restaurar.`;
        }
        openDialog(deleteDialog);
      });
    });

    root.querySelectorAll("dialog").forEach((dialog) => {
      dialog.addEventListener("click", (event) => {
        if (event.target !== dialog) return;
        const rect = dialog.getBoundingClientRect();
        const inside =
          event.clientX >= rect.left &&
          event.clientX <= rect.right &&
          event.clientY >= rect.top &&
          event.clientY <= rect.bottom;
        if (!inside) dialog.close?.();
      });
    });

    // If upload validation failed after a POST, reopen the upload form.
    if (root.querySelector(".app-field__error") && uploadDialog) {
      openDialog(uploadDialog);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDocumentsWorkspace, { once: true });
  } else {
    initDocumentsWorkspace();
  }

  document.addEventListener("dirtec:workspace:loaded", initDocumentsWorkspace);
})();
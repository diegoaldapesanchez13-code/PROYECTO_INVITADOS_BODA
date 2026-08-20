document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-task-workspace]");
  if (!root) return;

  const form = root.querySelector("[data-kanban-form]");
  if (!form) return;

  let dragging = null;

  root.querySelectorAll(".task-card[draggable='true']").forEach((card) => {
    card.addEventListener("dragstart", (event) => {
      dragging = card;
      card.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.dataset.taskId || "");
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("is-dragging");
      root.querySelectorAll("[data-dropzone]").forEach((zone) => zone.classList.remove("is-over"));
      dragging = null;
    });
  });

  root.querySelectorAll("[data-dropzone]").forEach((zone) => {
    zone.addEventListener("dragover", (event) => {
      if (!dragging) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      zone.classList.add("is-over");
    });

    zone.addEventListener("dragleave", () => zone.classList.remove("is-over"));

    zone.addEventListener("drop", (event) => {
      if (!dragging) return;
      event.preventDefault();
      zone.classList.remove("is-over");

      const taskId = dragging.dataset.taskId;
      const state = zone.dataset.dropzone;
      const current = dragging.closest("[data-state]")?.dataset.state;
      if (!taskId || !state || state === current) return;

      form.querySelector("[name='tarea_id']").value = taskId;
      form.querySelector("[name='estado']").value = state;
      form.submit();
    });
  });
});

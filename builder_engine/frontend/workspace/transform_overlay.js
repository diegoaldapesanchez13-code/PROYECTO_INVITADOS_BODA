export function createTransformOverlay() {
    const overlay = document.createElement("div");
    overlay.className = "engine-transform-overlay";
    overlay.hidden = true;
    overlay.innerHTML = `
        <div class="engine-transform-box">
            <button
                type="button"
                class="engine-transform-handle resize nw"
                data-transform-mode="resize"
                data-handle="nw"
                aria-label="Redimensionar desde la esquina superior izquierda"
            ></button>
            <button
                type="button"
                class="engine-transform-handle resize ne"
                data-transform-mode="resize"
                data-handle="ne"
                aria-label="Redimensionar desde la esquina superior derecha"
            ></button>
            <button
                type="button"
                class="engine-transform-handle resize sw"
                data-transform-mode="resize"
                data-handle="sw"
                aria-label="Redimensionar desde la esquina inferior izquierda"
            ></button>
            <button
                type="button"
                class="engine-transform-handle resize se"
                data-transform-mode="resize"
                data-handle="se"
                aria-label="Redimensionar desde la esquina inferior derecha"
            ></button>
            <button
                type="button"
                class="engine-transform-handle rotate"
                data-transform-mode="rotate"
                aria-label="Rotar elemento"
            >↻</button>
        </div>
    `;
    return overlay;
}

/**
 * El overlay y el elemento deben compartir el mismo contenedor:
 * .engine-live-canvas.
 */
export function positionTransformOverlay(overlay, element, liveCanvas) {
    if (!overlay || !element || !liveCanvas) {
        if (overlay) overlay.hidden = true;
        return;
    }

    const canvasRect = liveCanvas.getBoundingClientRect();
    const elementRect = element.getBoundingClientRect();

    const left = (
        elementRect.left
        - canvasRect.left
        + liveCanvas.scrollLeft
    );
    const top = (
        elementRect.top
        - canvasRect.top
        + liveCanvas.scrollTop
    );

    overlay.hidden = false;
    overlay.style.left = `${left}px`;
    overlay.style.top = `${top}px`;
    overlay.style.width = `${elementRect.width}px`;
    overlay.style.height = `${elementRect.height}px`;
}

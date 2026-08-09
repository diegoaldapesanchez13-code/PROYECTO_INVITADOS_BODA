export class NavigationResolver {
    constructor(options = {}) {
        this.root = options.root || null;
    }

    setRoot(root) {
        this.root = root || null;
        return this;
    }

    resolve(canvasId, options = {}) {
        const root = options.root || this.root;
        const normalizedId = String(canvasId || "").trim();

        if (!root || !normalizedId) {
            return null;
        }

        if (typeof root.querySelectorAll !== "function") {
            return null;
        }

        const candidates = root.querySelectorAll(
            "[data-r3-canvas-id]"
        );

        for (const element of candidates) {
            if (
                String(
                    element?.dataset?.r3CanvasId
                    || element?.getAttribute?.(
                        "data-r3-canvas-id"
                    )
                    || ""
                ) === normalizedId
            ) {
                return element;
            }
        }

        return null;
    }
}

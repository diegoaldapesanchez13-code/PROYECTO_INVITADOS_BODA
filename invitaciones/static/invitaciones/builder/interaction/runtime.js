import {
    NavigationEngine,
} from "../navigation/index.js";

export class BrowserInteractionRuntime {
    constructor(options = {}) {
        this.windowRef =
            options.windowRef
            ?? globalThis.window
            ?? null;

        this.navigationEngine =
            options.navigationEngine
            || new NavigationEngine({
                root: options.documentRoot || null,
            });
    }

    setDocumentRoot(root) {
        this.navigationEngine
            ?.setRoot?.(root);

        return this;
    }

    openUrl(url, options = {}) {
        const {
            openInNewTab = false,
        } = options;

        if (!this.windowRef) {
            return {
                executed: false,
                reason: "browser-unavailable",
                url,
                openInNewTab:
                    Boolean(openInNewTab),
            };
        }

        if (openInNewTab) {
            const opened =
                this.windowRef.open(
                    url,
                    "_blank",
                    "noopener,noreferrer"
                );

            if (opened) {
                try {
                    opened.opener = null;
                } catch {
                    // Algunos navegadores no permiten modificar opener.
                }
            }

            return {
                executed: Boolean(opened),
                reason: opened
                    ? null
                    : "popup-blocked",
                url,
                openInNewTab: true,
            };
        }

        if (
            this.windowRef.location
            && typeof this.windowRef.location.assign
                === "function"
        ) {
            this.windowRef.location.assign(url);

            return {
                executed: true,
                reason: null,
                url,
                openInNewTab: false,
            };
        }

        return {
            executed: false,
            reason: "navigation-unavailable",
            url,
            openInNewTab: false,
        };
    }

    navigateCanvas(canvasId, options = {}) {
        if (
            !this.navigationEngine
            || typeof this.navigationEngine
                .navigateToCanvas
                !== "function"
        ) {
            return {
                executed: false,
                reason: "navigation-engine-unavailable",
                canvasId:
                    String(canvasId || ""),
            };
        }

        return this.navigationEngine
            .navigateToCanvas(
                canvasId,
                options
            );
    }
}

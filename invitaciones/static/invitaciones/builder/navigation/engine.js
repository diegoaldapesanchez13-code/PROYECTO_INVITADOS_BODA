import {
    NavigationResolver,
} from "./resolver.js";

import {
    ScrollService,
} from "./scroll_service.js";

export class NavigationEngine {
    constructor(options = {}) {
        this.resolver =
            options.resolver
            || new NavigationResolver({
                root: options.root || null,
            });

        this.scrollService =
            options.scrollService
            || new ScrollService();
    }

    setRoot(root) {
        this.resolver.setRoot?.(root);
        return this;
    }

    navigateToCanvas(canvasId, options = {}) {
        const normalizedId =
            String(canvasId || "").trim();

        if (!normalizedId) {
            return {
                executed: false,
                reason: "canvas-id-required",
                canvasId: "",
            };
        }

        const element = this.resolver.resolve(
            normalizedId,
            {
                root: options.root || null,
            }
        );

        if (!element) {
            return {
                executed: false,
                reason: "canvas-not-found",
                canvasId: normalizedId,
            };
        }

        const scrollResult =
            this.scrollService.scrollTo(
                element,
                {
                    behavior:
                        options.behavior
                        || "smooth",
                    block:
                        options.block
                        || "start",
                    inline:
                        options.inline
                        || "nearest",
                }
            );

        return {
            ...scrollResult,
            canvasId: normalizedId,
        };
    }
}

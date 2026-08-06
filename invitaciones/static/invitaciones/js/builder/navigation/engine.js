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

    navigateToSection(sectionId, options = {}) {
        const normalizedId =
            String(sectionId || "").trim();

        if (!normalizedId) {
            return {
                executed: false,
                reason: "section-id-required",
                sectionId: "",
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
                reason: "section-not-found",
                sectionId: normalizedId,
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
            sectionId: normalizedId,
        };
    }
}

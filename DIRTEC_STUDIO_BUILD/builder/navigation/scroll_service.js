export class ScrollService {
    scrollTo(element, options = {}) {
        const {
            behavior = "smooth",
            block = "start",
            inline = "nearest",
        } = options;

        if (
            !element
            || typeof element.scrollIntoView
                !== "function"
        ) {
            return {
                executed: false,
                reason: "scroll-unavailable",
                behavior,
                block,
                inline,
            };
        }

        element.scrollIntoView({
            behavior,
            block,
            inline,
        });

        return {
            executed: true,
            reason: null,
            behavior,
            block,
            inline,
        };
    }
}

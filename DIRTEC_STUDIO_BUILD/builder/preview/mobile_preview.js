import { UniversalRenderer } from "../renderer/renderer.js";
import { ExperienceController } from "../experience/controller.js";

export const PREVIEW_DEVICES = Object.freeze({
    iphone_13: { label: "iPhone 13 / 14", width: 390, height: 844 },
    iphone_se: { label: "iPhone SE", width: 375, height: 667 },
    android: { label: "Android", width: 412, height: 915 },
});

export class MobilePreview {
    constructor({
        root,
        state,
        assetResolver,
        rsvpProvider = null,
        invitationContext = {},
        eventContext = {},
    }) {
        if (!(root instanceof Element)) throw new TypeError("root inválido para MobilePreview.");
        this.root = root;
        this.state = state;
        this.assetResolver = assetResolver;
        this.experienceController = null;
        this.deviceKey = "iphone_13";
        this.renderer = new UniversalRenderer({
            editable: false,
            device: "mobile",
            assetResolver,
            rsvpProvider,
            invitationContext,
            eventContext,
            onInteractionError: (error) => console.error("Preview interaction error", error),
        });
        this.bind();
        this.setDevice(this.deviceKey);
    }

    bind() {
        this.root.querySelector("[data-r3-preview-close]")?.addEventListener("click", () => this.close());
        this.root.querySelector("[data-r3-preview-backdrop]")?.addEventListener("click", () => this.close());
        this.root.querySelector("[data-r3-preview-device]")?.addEventListener("change", (event) => this.setDevice(event.target.value));
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && this.isOpen()) this.close();
        });
    }

    isOpen() { return !this.root.hidden; }

    open(options = {}) {
        const surface = this.root.querySelector("[data-r3-preview-surface]");
        const screen = this.root.querySelector("[data-r3-preview-screen]") || this.root;
        this.root.hidden = false;
        document.body.classList.add("r3-preview-open");
        this.experienceController?.dispose();
        this.experienceController = null;

        if (options.experience) {
            this.experienceController = new ExperienceController({
                document: this.state.document,
                root: screen,
                invitationElement: surface,
                assetResolver: (assetId) => this.#assetForExperience(assetId),
                logger: console,
                renderInvitation: () => {
                    this.renderer.mount(surface, this.state.document);
                },
            });
            this.experienceController.start();
        } else {
            this.renderer.mount(surface, this.state.document);
            surface.hidden = false;
        }
        surface.scrollTop = 0;
    }

    close() {
        this.experienceController?.dispose();
        this.experienceController = null;
        this.renderer.stopCountdownTicker?.();
        this.root.hidden = true;
        document.body.classList.remove("r3-preview-open");
    }

    refresh() {
        if (this.isOpen()) this.renderer.update(this.state.document);
    }

    restartExperience() {
        if (this.isOpen()) {
            this.open({ experience: true });
        }
    }

    setDevice(key) {
        const device = PREVIEW_DEVICES[key] || PREVIEW_DEVICES.iphone_13;
        this.deviceKey = PREVIEW_DEVICES[key] ? key : "iphone_13";
        const frame = this.root.querySelector("[data-r3-preview-frame]");
        if (frame) {
            frame.style.setProperty("--r3-preview-width", `${device.width}px`);
            frame.style.setProperty("--r3-preview-height", `${device.height}px`);
        }
        const select = this.root.querySelector("[data-r3-preview-device]");
        if (select) select.value = this.deviceKey;
        this.renderer.setDevice("mobile");
    }

    #assetForExperience(assetId) {
        const url = this.assetResolver?.(assetId);
        return url
            ? { id: assetId, url }
            : null;
    }
}

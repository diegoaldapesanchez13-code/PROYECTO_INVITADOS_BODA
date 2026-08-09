import { UniversalRenderer } from "../renderer/renderer.js";

export const PREVIEW_DEVICES = Object.freeze({
    iphone_13: { label: "iPhone 13 / 14", width: 390, height: 844 },
    iphone_se: { label: "iPhone SE", width: 375, height: 667 },
    android: { label: "Android", width: 412, height: 915 },
});

export class MobilePreview {
    constructor({ root, state, assetResolver, rsvpProvider = null, invitationContext = {} }) {
        if (!(root instanceof Element)) throw new TypeError("root inválido para MobilePreview.");
        this.root = root;
        this.state = state;
        this.deviceKey = "iphone_13";
        this.renderer = new UniversalRenderer({
            editable: false,
            device: "mobile",
            assetResolver,
            rsvpProvider,
            invitationContext,
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

    open() {
        const surface = this.root.querySelector("[data-r3-preview-surface]");
        this.root.hidden = false;
        document.body.classList.add("r3-preview-open");
        this.renderer.mount(surface, this.state.document);
        surface.scrollTop = 0;
    }

    close() {
        this.renderer.stopCountdownTicker?.();
        this.root.hidden = true;
        document.body.classList.remove("r3-preview-open");
    }

    refresh() {
        if (this.isOpen()) this.renderer.update(this.state.document);
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
}

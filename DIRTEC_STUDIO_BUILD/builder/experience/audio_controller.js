export class AudioController {
    constructor(options = {}) {
        this.document = options.document || globalThis.document || null;
        this.root = options.root || null;
        this.audio = options.audio || {};
        this.assetResolver = options.assetResolver || (() => null);
        this.logger = options.logger || console;
        this.element = null;
        this.controlElement = null;
        this.playing = false;
        this.blocked = false;
        this.toggle = this.toggle.bind(this);
    }

    isEnabled() {
        return Boolean(this.audio.enabled && this.audio.assetId);
    }

    async start(reason = "MANUAL") {
        if (!this.isEnabled()) {
            return false;
        }

        const policy = this.audio.startPolicy || "AFTER_INTRO";
        if (policy === "MANUAL" && reason !== "MANUAL") {
            return false;
        }

        if (
            policy === "ON_OPEN_GESTURE"
            && reason !== "OPEN_GESTURE"
            && reason !== "MANUAL"
        ) {
            return false;
        }

        const element = this.#ensureElement();
        if (!element) {
            return false;
        }

        try {
            const result = element.play?.();
            if (result && typeof result.then === "function") {
                await result;
            }
            this.blocked = false;
            this.playing = true;
            this.#ensureControl();
            this.#syncControl();
            return true;
        } catch (error) {
            this.blocked = true;
            this.playing = false;
            this.#ensureControl();
            this.#syncControl();
            this.logger.warn?.("Experience audio blocked", error);
            return false;
        }
    }

    pause() {
        this.element?.pause?.();
        this.playing = false;
        this.#syncControl();
    }

    toggle() {
        if (this.playing) {
            this.pause();
            return;
        }

        this.start("MANUAL");
    }

    dispose() {
        this.pause();
        if (this.element) {
            this.element.src = "";
        }
        this.controlElement?.remove?.();
        if (this.controlElement?.parentNode?.removeChild) {
            this.controlElement.parentNode.removeChild(this.controlElement);
        }
        this.element = null;
        this.controlElement = null;
    }

    #ensureElement() {
        if (this.element) {
            return this.element;
        }

        const asset = this.assetResolver(this.audio.assetId);
        const src = asset?.url || asset?.src || "";
        if (!src || !this.document?.createElement) {
            return null;
        }

        const element = this.document.createElement("audio");
        element.src = src;
        element.loop = this.audio.loop !== false;
        element.volume = Number.isFinite(this.audio.volume)
            ? this.audio.volume
            : 0.7;
        element.preload = "auto";

        this.element = element;
        return element;
    }

    #ensureControl() {
        if (
            this.controlElement
            || this.audio.showControl === false
            || !this.root?.append
            || !this.document?.createElement
        ) {
            return this.controlElement;
        }

        const control = this.document.createElement("button");
        control.type = "button";
        control.className = "experience-audio-control";
        control.addEventListener?.("click", this.toggle);
        this.root.append(control);
        this.controlElement = control;
        this.#syncControl();
        return control;
    }

    #syncControl() {
        if (!this.controlElement) {
            return;
        }

        this.controlElement.textContent = this.playing
            ? "Pausar"
            : "Reproducir";
        this.controlElement.dataset.audioPlaying = this.playing
            ? "true"
            : "false";
        this.controlElement.dataset.audioBlocked = this.blocked
            ? "true"
            : "false";
    }
}

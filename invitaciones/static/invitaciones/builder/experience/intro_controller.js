export class IntroController {
    constructor(options = {}) {
        this.document = options.document || globalThis.document || null;
        this.root = options.root || null;
        this.intro = options.intro || {};
        this.assetResolver = options.assetResolver || (() => null);
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});
        this.overlay = null;
        this.mediaElement = null;
        this.completed = false;
        this.videoStarted = false;
        this.open = this.open.bind(this);
        this.skip = this.skip.bind(this);
    }

    hasIntro() {
        return Boolean(
            this.intro.enabled
            && this.intro.mode
            && this.intro.mode !== "NONE"
        );
    }

    mount() {
        if (!this.hasIntro()) {
            this.complete();
            return null;
        }

        if (this.#requiresAsset() && !this.#resolveAssetUrl()) {
            this.complete();
            return null;
        }

        try {
            const overlay = this.#createOverlay();
            this.root?.append?.(overlay);
            this.overlay = overlay;
            return overlay;
        } catch (error) {
            this.onError(error);
            this.complete();
            return null;
        }
    }

    open(event = null) {
        event?.stopPropagation?.();
        if (this.completed) {
            return;
        }

        if (this.intro.mode === "VIDEO") {
            this.#playVideo(event);
            return;
        }

        this.overlay?.classList?.add?.("experience-intro--opening");
        if (this.overlay?.className) {
            this.overlay.className += " experience-intro--opening";
        }
        if (this.overlay?.dataset) {
            this.overlay.dataset.experienceIntroState = "opening";
        }

        const duration = Number(this.intro.transition?.durationMs || 0);
        if (duration > 0) {
            globalThis.setTimeout?.(
                () => this.complete(event),
                duration,
            );
            return;
        }

        this.complete(event);
    }

    complete(event = null) {
        if (this.completed) {
            return;
        }
        this.completed = true;
        this.dispose();
        this.onComplete({
            userGesture: Boolean(event),
            mode: this.intro.mode || "NONE",
        });
    }

    dispose() {
        this.mediaElement?.pause?.();
        this.overlay?.remove?.();
        if (this.overlay?.parentNode?.removeChild) {
            this.overlay.parentNode.removeChild(this.overlay);
        }
        this.mediaElement = null;
        this.overlay = null;
    }

    skip(event = null) {
        event?.stopPropagation?.();
        this.complete(event);
    }

    #createOverlay() {
        if (this.intro.mode === "ENVELOPE") {
            return this.#createEnvelopeOverlay();
        }

        if (["IMAGE", "GIF"].includes(this.intro.mode)) {
            return this.#createImageOverlay();
        }

        if (this.intro.mode === "VIDEO") {
            return this.#createVideoOverlay();
        }

        const overlay = this.document.createElement("section");
        overlay.className = "experience-intro";
        overlay.dataset.experienceIntroMode = this.intro.mode;
        overlay.setAttribute("aria-modal", "true");

        const label = this.document.createElement("button");
        label.type = "button";
        label.className = "experience-intro__open";
        label.textContent = this.intro.showOpenLabel === false
            ? ""
            : this.intro.openLabel || "Abrir invitación";
        label.addEventListener?.("click", this.open);

        if (this.intro.clickAnywhere !== false) {
            overlay.addEventListener?.("click", this.open);
        }

        overlay.append(label);
        return overlay;
    }

    #createVideoOverlay() {
        const asset = this.assetResolver(this.intro.assetId);
        const poster = this.assetResolver(this.intro.posterAssetId);
        const src = asset?.url || asset?.src || "";
        const posterSrc = poster?.url || poster?.src || "";
        const options = this.intro.video || {};

        const overlay = this.document.createElement("section");
        overlay.className = "experience-intro experience-intro--video";
        overlay.dataset.experienceIntroMode = "VIDEO";
        overlay.dataset.experienceIntroState = "ready";
        overlay.setAttribute("aria-modal", "true");

        if (overlay.style) {
            overlay.style.backgroundColor =
                this.intro.backgroundColor || "#000000";
        }

        const video = this.document.createElement("video");
        video.className = "experience-intro__video";
        video.src = src;
        video.poster = posterSrc;
        video.controls = Boolean(options.controls);
        video.muted = Boolean(options.muted);
        video.playsInline = options.playsInline !== false;
        video.loop = false;
        video.preload = "metadata";
        if (video.setAttribute && video.playsInline) {
            video.setAttribute("playsinline", "");
        }
        if (video.style) {
            applyMediaPlacement(video, this.intro);
        }
        video.addEventListener?.("ended", () => {
            if (options.transitionOnEnded !== false) {
                this.complete();
            }
        });
        video.addEventListener?.("error", () => this.complete());
        video.onerror = () => this.complete();
        video.onended = () => {
            if (options.transitionOnEnded !== false) {
                this.complete();
            }
        };

        this.mediaElement = video;

        const play = this.document.createElement("button");
        play.type = "button";
        play.className = "experience-intro__open experience-intro__video-play";
        play.textContent = this.intro.showOpenLabel === false
            ? ""
            : this.intro.openLabel || "Abrir invitación";
        play.addEventListener?.("click", this.open);

        overlay.append(video, play);

        if (this.intro.allowSkip !== false) {
            const skip = this.document.createElement("button");
            skip.type = "button";
            skip.className = "experience-intro__skip";
            skip.textContent = "Saltar";
            skip.addEventListener?.("click", this.skip);
            overlay.append(skip);
        }

        if (this.intro.clickAnywhere !== false) {
            overlay.addEventListener?.("click", this.open);
        }

        return overlay;
    }

    #createImageOverlay() {
        const asset = this.assetResolver(this.intro.assetId);
        const src = asset?.url || asset?.src || "";
        const modeClass = this.intro.mode.toLowerCase();

        const overlay = this.document.createElement("section");
        overlay.className = `experience-intro experience-intro--media experience-intro--${modeClass}`;
        overlay.dataset.experienceIntroMode = this.intro.mode;
        overlay.dataset.experienceIntroState = "ready";
        overlay.setAttribute("aria-modal", "true");

        if (overlay.style) {
            overlay.style.backgroundColor =
                this.intro.backgroundColor || "#000000";
        }

        const image = this.document.createElement("img");
        image.className = "experience-intro__media";
        image.src = src;
        image.alt = "";
        image.decoding = "async";
        if (image.style) {
            applyMediaPlacement(image, this.intro);
        }
        image.onerror = () => this.complete();

        const label = this.document.createElement("button");
        label.type = "button";
        label.className = "experience-intro__open experience-intro__media-open";
        label.textContent = this.intro.showOpenLabel === false
            ? ""
            : this.intro.openLabel || "Abrir invitación";
        label.addEventListener?.("click", this.open);

        overlay.append(image, label);

        if (this.intro.clickAnywhere !== false) {
            overlay.addEventListener?.("click", this.open);
        }

        return overlay;
    }

    #createEnvelopeOverlay() {
        const envelope = this.intro.envelope || {};
        const palette = envelope.palette || "CLASSIC";
        const background = this.assetResolver(envelope.backgroundAssetId);
        const seal = this.assetResolver(envelope.sealAssetId);

        const overlay = this.document.createElement("section");
        overlay.className = `experience-intro experience-intro--envelope experience-intro--palette-${palette.toLowerCase()}`;
        overlay.dataset.experienceIntroMode = "ENVELOPE";
        overlay.dataset.experienceIntroState = "ready";
        overlay.setAttribute("aria-modal", "true");

        const backgroundUrl = background?.url || background?.src || "";
        if (backgroundUrl && overlay.style) {
            overlay.style.backgroundImage = `url("${backgroundUrl}")`;
        }

        const shell = this.document.createElement("div");
        shell.className = "experience-envelope";

        const flap = this.document.createElement("div");
        flap.className = "experience-envelope__flap";

        const body = this.document.createElement("div");
        body.className = "experience-envelope__body";

        const monogram = this.document.createElement("div");
        monogram.className = "experience-envelope__monogram";
        monogram.textContent = envelope.monogram || "";

        const message = this.document.createElement("p");
        message.className = "experience-envelope__message";
        message.textContent = envelope.message || "";

        const open = this.document.createElement("button");
        open.type = "button";
        open.className = "experience-intro__open experience-envelope__open";
        open.textContent = this.intro.showOpenLabel === false
            ? ""
            : this.intro.openLabel || "Abrir invitación";
        open.addEventListener?.("click", this.open);

        const sealUrl = seal?.url || seal?.src || "";
        if (sealUrl) {
            const sealImage = this.document.createElement("img");
            sealImage.className = "experience-envelope__seal";
            sealImage.src = sealUrl;
            sealImage.alt = "";
            body.append(sealImage);
        } else {
            const sealFallback = this.document.createElement("div");
            sealFallback.className = "experience-envelope__seal-fallback";
            sealFallback.textContent = envelope.monogram || "";
            body.append(sealFallback);
        }

        body.append(monogram, message, open);
        shell.append(flap, body);
        overlay.append(shell);

        if (this.intro.clickAnywhere !== false) {
            overlay.addEventListener?.("click", this.open);
        }

        return overlay;
    }

    #requiresAsset() {
        return ["IMAGE", "GIF", "VIDEO"].includes(this.intro.mode);
    }

    #resolveAssetUrl() {
        const asset = this.assetResolver(this.intro.assetId);
        return asset?.url || asset?.src || "";
    }

    async #playVideo(event = null) {
        event?.stopPropagation?.();
        if (this.completed || this.videoStarted) {
            return;
        }

        const video = this.mediaElement;
        if (!video) {
            this.complete(event);
            return;
        }

        this.videoStarted = true;
        if (this.overlay?.dataset) {
            this.overlay.dataset.experienceIntroState = "playing";
        }

        try {
            const result = video.play?.();
            if (result && typeof result.then === "function") {
                await result;
            }
        } catch (error) {
            this.onError(error);
            this.complete(event);
        }
    }
}

function applyMediaPlacement(element, intro = {}) {
    const position = intro.mediaPosition || {};
    const x = clampNumber(position.x, 50, 0, 100);
    const y = clampNumber(position.y, 50, 0, 100);
    const scale = clampNumber(intro.mediaScale, 1, 0.5, 2);

    element.style.objectFit = intro.fit || "cover";
    element.style.objectPosition = `${x}% ${y}%`;
    element.style.transform = `scale(${scale})`;
    element.style.transformOrigin = `${x}% ${y}%`;
}

function clampNumber(value, fallback, min, max) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return fallback;
    }
    return Math.min(max, Math.max(min, number));
}


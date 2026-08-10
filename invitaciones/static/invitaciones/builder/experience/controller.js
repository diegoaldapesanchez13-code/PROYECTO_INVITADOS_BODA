import {
    normalizeDocumentV4,
} from "../core/schema_v4.js?v=f4-native-v4-freeze";
import { AudioController } from "./audio_controller.js";
import { IntroController } from "./intro_controller.js";

export const EXPERIENCE_STATES = Object.freeze({
    IDLE: "IDLE",
    INTRO_READY: "INTRO_READY",
    INTRO_PLAYING: "INTRO_PLAYING",
    INTRO_COMPLETE: "INTRO_COMPLETE",
    INVITATION_VISIBLE: "INVITATION_VISIBLE",
    ERROR: "ERROR",
});

export class ExperienceController {
    constructor(options = {}) {
        this.document = normalizeDocumentV4(options.document || {});
        this.root = options.root || null;
        this.invitationElement = options.invitationElement || null;
        this.renderInvitation = options.renderInvitation || null;
        this.logger = options.logger || console;
        this.state = EXPERIENCE_STATES.IDLE;

        this.assetResolver =
            options.assetResolver
            || ((assetId) => this.#resolveAsset(assetId));

        const ownerDocument =
            options.domDocument
            || this.root?.ownerDocument
            || this.invitationElement?.ownerDocument
            || globalThis.document
            || null;

        this.audioController = new AudioController({
            document: ownerDocument,
            root: this.root,
            audio: this.document.experience.audio,
            assetResolver: this.assetResolver,
            logger: this.logger,
        });

        this.introController = new IntroController({
            document: ownerDocument,
            root: this.root,
            intro: this.document.experience.intro,
            assetResolver: this.assetResolver,
            logger: this.logger,
            onError: (error) => this.#failOpen(error),
            onComplete: (payload) => this.#completeIntro(payload),
        });
    }

    start() {
        try {
            this.#renderInvitation();

            if (!this.introController.hasIntro()) {
                this.#completeIntro({ userGesture: false, mode: "NONE" });
                return this.state;
            }

            this.#hideInvitation();
            this.#setState(EXPERIENCE_STATES.INTRO_READY);
            const overlay = this.introController.mount();

            if (overlay) {
                this.#setState(EXPERIENCE_STATES.INTRO_PLAYING);
            }

            return this.state;
        } catch (error) {
            this.#failOpen(error);
            return this.state;
        }
    }

    dispose() {
        this.introController.dispose();
        this.audioController.dispose();
    }

    #completeIntro(payload = {}) {
        this.#setState(EXPERIENCE_STATES.INTRO_COMPLETE);
        this.#revealInvitation();

        const reason = payload.userGesture
            ? "OPEN_GESTURE"
            : "AFTER_INTRO";
        this.audioController.start(reason);
    }

    #failOpen(error) {
        this.logger.warn?.("Experience fallback", error);
        this.#setState(EXPERIENCE_STATES.ERROR);
        this.#revealInvitation();
    }

    #renderInvitation() {
        if (typeof this.renderInvitation === "function") {
            this.renderInvitation(this.invitationElement);
        }
    }

    #hideInvitation() {
        if (this.invitationElement) {
            this.invitationElement.hidden = true;
            this.invitationElement.dataset.experienceVisible = "false";
        }
    }

    #revealInvitation() {
        if (this.invitationElement) {
            this.invitationElement.hidden = false;
            this.invitationElement.dataset.experienceVisible = "true";
        }
        this.#setState(EXPERIENCE_STATES.INVITATION_VISIBLE);
    }

    #setState(next) {
        this.state = next;
    }

    #resolveAsset(assetId) {
        if (!assetId) {
            return null;
        }

        return (this.document.assets || []).find(
            (asset) => String(asset.id) === String(assetId),
        ) || null;
    }
}

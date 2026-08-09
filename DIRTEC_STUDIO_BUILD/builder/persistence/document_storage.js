import {
    canonicalizeDocumentV4,
} from "../core/runtime_v4.js";

const NON_DOCUMENT_EVENTS =
    new Set([
        "selection:change",
        "selection:clear",
    ]);

export class BuilderDocumentStorage {
    constructor(options = {}) {
        const {
            key =
                "dirtec.builder.document.v1",
            storage =
                globalThis.localStorage,
            canonicalV4 = true,
        } = options;

        this.key = key;
        this.storage = storage;
        this.canonicalV4 =
            Boolean(canonicalV4);
    }

    load() {
        if (!this.storage) {
            return null;
        }

        try {
            const raw =
                this.storage.getItem(
                    this.key
                );

            if (!raw) {
                return null;
            }

            const parsed =
                JSON.parse(raw);

            if (
                !parsed
                || typeof parsed
                    !== "object"
            ) {
                return null;
            }

            if (this.canonicalV4) {
                return canonicalizeDocumentV4(
                    parsed
                );
            }

            if (
                !Array.isArray(parsed.canvases)
                || !Array.isArray(parsed.nodes)
            ) {
                return null;
            }

            return parsed;
        } catch (error) {
            console.warn(
                "No fue posible restaurar el documento.",
                error
            );

            return null;
        }
    }

    save(document) {
        if (!this.storage) {
            return false;
        }

        try {
            const payload =
                this.canonicalV4
                    ? canonicalizeDocumentV4(
                        document
                    )
                    : document;

            this.storage.setItem(
                this.key,
                JSON.stringify(payload)
            );

            return true;
        } catch (error) {
            console.warn(
                "No fue posible guardar el documento.",
                error
            );

            return false;
        }
    }

    clear() {
        if (!this.storage) {
            return false;
        }

        this.storage.removeItem(
            this.key
        );

        return true;
    }
}

export function connectDocumentPersistence(
    options = {}
) {
    const {
        state,
        storage,
        debounceMs = 80,
        onSaved = null,
        onError = null,
    } = options;

    if (!state || !storage) {
        throw new Error(
            "connectDocumentPersistence requiere state y storage."
        );
    }

    let timer = null;
    let stopped = false;

    const persist =
        (document) => {
            if (stopped) {
                return;
            }

            try {
                const saved =
                    storage.save(document);

                if (saved) {
                    onSaved?.(document);
                }
            } catch (error) {
                onError?.(error);
            }
        };

    const unsubscribe =
        state.subscribe(
            (event) => {
                if (
                    NON_DOCUMENT_EVENTS.has(
                        event.type
                    )
                ) {
                    return;
                }

                if (timer !== null) {
                    clearTimeout(timer);
                }

                timer = setTimeout(
                    () => {
                        timer = null;
                        persist(
                            event.document
                        );
                    },
                    Math.max(
                        Number(debounceMs) || 0,
                        0
                    )
                );
            }
        );

    return () => {
        stopped = true;

        if (timer !== null) {
            clearTimeout(timer);
            timer = null;
        }

        unsubscribe();
    };
}
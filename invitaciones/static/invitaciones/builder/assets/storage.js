export class AssetStorage {
    constructor(options = {}) {
        const {
            key =
                "dirtec.builder.assets.v1",
            storage =
                globalThis.localStorage,
        } = options;

        this.key = key;
        this.storage = storage;
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

            return {
                uploads:
                    Array.isArray(
                        parsed.uploads
                    )
                        ? parsed.uploads
                        : [],
                recentIds:
                    Array.isArray(
                        parsed.recentIds
                    )
                        ? parsed.recentIds
                        : [],
            };
        } catch {
            return null;
        }
    }

    save(payload) {
        if (!this.storage) {
            return false;
        }

        try {
            this.storage.setItem(
                this.key,
                JSON.stringify(payload)
            );

            return true;
        } catch (error) {
            console.warn(
                "No fue posible guardar assets.",
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

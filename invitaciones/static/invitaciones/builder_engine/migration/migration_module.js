import { MIGRATION_MODULE_NAME } from "./constants.js";
import {
    isLegacyMigrationPending,
    migrateLegacyDocument,
} from "./legacy_document_migrator.js";

export class MigrationModule {
    key = MIGRATION_MODULE_NAME;
    version = "1.0.0";
    dependencies = Object.freeze(["persistence"]);

    constructor(options = {}) {
        this.options = options;
        this.lastReport = null;
    }

    migrateIfNeeded(app, options = {}) {
        const current = app.getDocument();
        if (!isLegacyMigrationPending(current)) {
            this.lastReport = {
                migrated: false,
                reason: "not-pending",
            };
            return this.lastReport;
        }

        const result = migrateLegacyDocument(current, {
            ...this.options,
            ...options,
        });

        if (result.migrated) {
            app.replaceDocument(result.document, {
                label: "Migrar diseño anterior",
                source: "migration",
                mergeKey: null,
                legacyMigration: true,
            });
        }

        this.lastReport = {
            migrated: result.migrated,
            ...result.report,
        };
        return this.lastReport;
    }

    start() {
        return this;
    }

    destroy() {
        this.lastReport = null;
    }
}

export function registerMigrationModule(app, options = {}) {
    const module = new MigrationModule(options);
    app.register(MIGRATION_MODULE_NAME, module, {
        replace: options.replace === true,
    });
    return module;
}

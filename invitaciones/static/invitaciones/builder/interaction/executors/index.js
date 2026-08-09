import {
    INTERACTION_TYPES,
} from "../defaults.js";

import {
    executeNone,
} from "./none.js";

import {
    executeUrl,
} from "./url.js";

import {
    executeGoogleMaps,
} from "./maps.js";

import {
    executeWhatsApp,
} from "./whatsapp.js";

import {
    executeCanvas,
} from "./canvas.js";

export function createDefaultInteractionExecutors() {
    return new Map([
        [INTERACTION_TYPES.NONE, executeNone],
        [INTERACTION_TYPES.URL, executeUrl],
        [INTERACTION_TYPES.GOOGLE_MAPS, executeGoogleMaps],
        [INTERACTION_TYPES.WHATSAPP, executeWhatsApp],
        [INTERACTION_TYPES.CANVAS, executeCanvas],
    ]);
}

export {
    executeNone,
    executeUrl,
    executeGoogleMaps,
    executeWhatsApp,
    executeCanvas,
};

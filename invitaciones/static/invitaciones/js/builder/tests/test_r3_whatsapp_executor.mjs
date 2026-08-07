import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
    InteractionEngine,
    validateWhatsAppRecipient,
    whatsappUrl,
} from "../interaction/index.js";

function whatsappNode(
    recipient,
    message = "",
    openInNewTab = true
) {
    return createNode(
        NODE_TYPES.IMAGE,
        {
            interaction: {
                enabled: true,
                action: {
                    type:
                        INTERACTION_TYPES
                            .WHATSAPP,
                    value: recipient,
                    target: message,
                    openInNewTab,
                },
            },
        }
    );
}

const calls = [];
const runtime = {
    openUrl(url, options) {
        calls.push({ url, options });

        return {
            executed: true,
            reason: null,
            url,
            openInNewTab:
                options.openInNewTab,
        };
    },
};

const engine = new InteractionEngine({
    runtime,
});

const withMessage = engine.execute(
    whatsappNode(
        "+52 (477) 123-4567",
        "Hola, confirmo mi asistencia."
    )
);

assert.equal(withMessage.handled, true);
assert.equal(withMessage.status, "executed");
assert.equal(
    withMessage.intent,
    "OPEN_WHATSAPP"
);
assert.equal(
    withMessage.payload.recipient,
    "524771234567"
);
assert.equal(
    withMessage.payload.message,
    "Hola, confirmo mi asistencia."
);
assert.equal(
    withMessage.payload.url,
    "https://wa.me/524771234567?text=Hola%2C%20confirmo%20mi%20asistencia."
);
assert.equal(
    withMessage.payload.openInNewTab,
    true
);
assert.equal(calls.length, 1);

const withoutMessage = engine.execute(
    whatsappNode(
        "005214771234567",
        "",
        false
    )
);

assert.equal(withoutMessage.handled, true);
assert.equal(withoutMessage.status, "executed");
assert.equal(
    withoutMessage.payload.recipient,
    "5214771234567"
);
assert.equal(
    withoutMessage.payload.url,
    "https://wa.me/5214771234567"
);
assert.equal(
    withoutMessage.payload.openInNewTab,
    false
);
assert.equal(calls.length, 2);

const fromWaMe = engine.execute(
    whatsappNode(
        "https://wa.me/5214771234567?text=ignorado"
    )
);

assert.equal(fromWaMe.handled, true);
assert.equal(
    fromWaMe.payload.recipient,
    "5214771234567"
);
assert.equal(calls.length, 3);

for (const invalidRecipient of [
    "",
    "123",
    "abcdef",
    "5214771234567890",
]) {
    const result = engine.execute(
        whatsappNode(invalidRecipient)
    );

    assert.equal(result.handled, false);
    assert.equal(result.status, "invalid");
    assert.equal(
        result.intent,
        "OPEN_WHATSAPP"
    );
}

assert.equal(calls.length, 3);
assert.equal(
    validateWhatsAppRecipient(
        "+52 477 123 4567"
    ).value,
    "524771234567"
);
assert.equal(
    validateWhatsAppRecipient("123").valid,
    false
);
assert.equal(
    whatsappUrl(
        "5214771234567",
        "Hola & gracias"
    ),
    "https://wa.me/5214771234567?text=Hola%20%26%20gracias"
);

console.log(
    "OK WhatsApp executor validates and navigates"
);

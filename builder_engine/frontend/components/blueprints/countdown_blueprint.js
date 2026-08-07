export function createCountdownBlueprint(factory) {
    if (!factory?.create) throw new TypeError("Countdown blueprint requiere ComponentFactory.");

    return {
        id: "countdown",
        version: "1.1.0",
        label: "Cuenta regresiva",
        rootType: "COUNTDOWN",
        create(context = {}) {
            const position = context.position || {};
            const root = factory.create("COUNTDOWN", {
                name: "Cuenta regresiva",
                content: {
                    targetDate: context.targetDate || "",
                    compositeVersion: 1,
                },
                style: {
                    x: Number(position.x ?? 50),
                    y: Number(position.y ?? 50),
                    width: Number(position.width ?? 92),
                    zIndex: Number(position.zIndex ?? 1),
                    layout: "grid",
                },
                children: [],
            }, context);

            const units = [
                ["days", "Días", "120"],
                ["hours", "Horas", "12"],
                ["minutes", "Minutos", "34"],
                ["seconds", "Segundos", "56"],
            ];

            root.children = units.map(([unit, label, previewValue]) => {
                const card = factory.create("CARD", {
                    name: label,
                    content: { countdownUnit: unit },
                    style: {
                        width: 22,
                        minHeight: 90,
                        backgroundColor: "rgba(255,255,255,.84)",
                        borderRadius: 16,
                        padding: 10,
                    },
                    children: [],
                }, context);

                card.children = [
                    factory.create("TEXT", {
                        name: `${label} · Número`,
                        content: {
                            text: previewValue,
                            binding: { source: "COUNTDOWN", unit, role: "value" },
                        },
                        style: {
                            width: 100,
                            fontSize: 34,
                            fontWeight: 700,
                            textAlign: "center",
                        },
                    }, context),
                    factory.create("TEXT", {
                        name: `${label} · Etiqueta`,
                        content: {
                            text: label,
                            binding: { source: "COUNTDOWN", unit, role: "label" },
                        },
                        style: {
                            width: 100,
                            fontSize: 12,
                            textAlign: "center",
                        },
                    }, context),
                ];
                return card;
            });

            return root;
        },
    };
}

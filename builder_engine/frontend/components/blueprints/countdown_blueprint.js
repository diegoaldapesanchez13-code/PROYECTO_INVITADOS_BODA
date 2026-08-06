export function createCountdownBlueprint(factory) {
    if (!factory?.create) throw new TypeError("Countdown blueprint requiere ComponentFactory.");

    return {
        id: "countdown",
        version: "1.0.0",
        label: "Cuenta regresiva",
        rootType: "COUNTDOWN",
        create(context = {}) {
            const root = factory.create("COUNTDOWN", {
                name: "Cuenta regresiva",
                content: {
                    targetDate: context.targetDate || "",
                    compositeVersion: 1,
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
                    children: [],
                }, context);

                card.children = [
                    factory.create("TEXT", {
                        name: `${label} · Número`,
                        content: {
                            text: previewValue,
                            binding: { source: "COUNTDOWN", unit, role: "value" },
                        },
                    }, context),
                    factory.create("TEXT", {
                        name: `${label} · Etiqueta`,
                        content: {
                            text: label,
                            binding: { source: "COUNTDOWN", unit, role: "label" },
                        },
                    }, context),
                ];
                return card;
            });

            return root;
        },
    };
}

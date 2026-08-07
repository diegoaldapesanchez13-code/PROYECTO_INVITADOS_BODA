export function createUniversalRendererFixture() {
    return {
        schemaVersion: 1,
        documentVersion: 1,
        metadata: { name: "Fixture universal" },
        canvases: [{
            id: "canvas-portada",
            name: "Portada",
            order: 1,
            visible: true,
            size: {
                responsive: {
                    mobile: { height: 1000 },
                    tablet: { height: 900 },
                    desktop: { height: 820 },
                },
            },
            background: { color: "#f5f1e8" },
            nodes: [
                {
                    id: "photo",
                    type: "IMAGE",
                    name: "Ubicación",
                    visible: true,
                    style: { zIndex: 1, borderRadius: 20, objectFit: "cover" },
                    layout: {
                        transform: {
                            x: 50, y: 38, width: 82, height: 42,
                            rotation: 0, opacity: 1,
                        },
                        responsive: {
                            tablet: { width: 60, height: 36 },
                            desktop: { width: 42, height: 42 },
                        },
                    },
                    content: {
                        url: "/media/location.jpg",
                        alt: "Abrir ubicación",
                    },
                    interaction: {
                        ariaLabel: "Abrir ubicación",
                        interactions: [{
                            trigger: "CLICK",
                            action: {
                                type: "GOOGLE_MAPS",
                                value: "https://maps.google.com/",
                                openInNewTab: true,
                            },
                        }],
                        states: { pressed: { scale: 0.97 } },
                    },
                    children: [],
                },
                {
                    id: "title",
                    type: "TEXT",
                    name: "Título",
                    visible: true,
                    style: {
                        zIndex: 2,
                        color: "#26362b",
                        fontSize: 42,
                        fontWeight: 700,
                        textAlign: "center",
                    },
                    layout: {
                        transform: {
                            x: 50, y: 70, width: 80, height: 10,
                            rotation: 0, opacity: 1,
                        },
                    },
                    content: { tag: "h1", text: "Fernando & Diego" },
                    children: [],
                },
                {
                    id: "card",
                    type: "CARD",
                    name: "Detalles",
                    visible: true,
                    style: {
                        zIndex: 3,
                        backgroundColor: "#ffffff",
                        borderRadius: 24,
                        padding: 16,
                        gap: 8,
                    },
                    layout: {
                        transform: {
                            x: 50, y: 86, width: 86, height: 18,
                            rotation: 0, opacity: 1,
                        },
                    },
                    children: [
                        {
                            id: "card-text",
                            type: "TEXT",
                            name: "Texto Card",
                            visible: true,
                            style: { zIndex: 1, fontSize: 18, textAlign: "center" },
                            layout: {
                                layoutMode: "FLOW",
                                transform: {
                                    x: 50, y: 50, width: 100, height: 6,
                                    rotation: 0, opacity: 1,
                                },
                            },
                            content: { text: "Nuestra celebración" },
                            children: [],
                        },
                    ],
                },
            ],
        }],
    };
}

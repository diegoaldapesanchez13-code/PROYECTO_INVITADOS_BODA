import { action, actionGroup, field, group } from "../controls.js";

const VIDEO_ASSET_TYPE = "VIDEO";

export function videoPanel() {
    return [
        group({
            id: "video-content",
            title: "Video / YouTube",
            description: "Pega un enlace de YouTube, selecciona un video de tu biblioteca o usa una URL directa.",
            fields: [
                field({
                    key: "videoSourceType",
                    label: "Fuente del video",
                    type: "select",
                    path: "content.sourceType",
                    options: [
                        ["youtube", "YouTube (iframe automático)"],
                        ["library", "Biblioteca / archivo subido"],
                        ["direct", "URL directa MP4 / WebM"],
                    ],
                }),
                field({
                    key: "videoYoutubeSource",
                    label: "Enlace de YouTube",
                    type: "textarea",
                    path: "content.source",
                    placeholder: "https://www.youtube.com/watch?v=...",
                    help: "Acepta watch, youtu.be, Shorts, Live y enlaces embed. El iframe se genera automáticamente.",
                    visibleWhen: ({ node }) => (node.content?.sourceType || "youtube") === "youtube",
                }),
                field({
                    key: "videoLibraryAsset",
                    label: "Video de la biblioteca",
                    type: "select",
                    path: "content.assetId",
                    options: ({ assets }) => libraryVideoOptions(assets),
                    help: "Selecciona un video que ya subiste desde Assets.",
                    visibleWhen: ({ node }) => node.content?.sourceType === "library",
                    onChange: ({ assets, current, value }) => {
                        const asset = assets?.get?.(value);
                        if (!asset) {
                            return {
                                content: {
                                    ...(current.content || {}),
                                    assetId: "",
                                    source: "",
                                    sourceType: "library",
                                },
                            };
                        }
                        return {
                            content: {
                                ...(current.content || {}),
                                assetId: asset.id,
                                source: asset.url,
                                sourceType: "library",
                                title: current.content?.title || asset.name,
                            },
                        };
                    },
                }),
                field({
                    key: "videoDirectSource",
                    label: "URL directa",
                    type: "textarea",
                    path: "content.source",
                    placeholder: "https://.../video.mp4",
                    visibleWhen: ({ node }) => node.content?.sourceType === "direct",
                }),
                field({
                    key: "videoPoster",
                    label: "Portada (URL)",
                    type: "text",
                    path: "content.poster",
                    placeholder: "https://.../portada.jpg",
                }),
                field({
                    key: "videoTitle",
                    label: "Título accesible",
                    type: "text",
                    path: "content.title",
                    placeholder: "Video de la invitación",
                }),
                field({ key: "videoAutoplay", label: "Autoplay", type: "checkbox", path: "content.autoplay" }),
                field({ key: "videoLoop", label: "Repetir", type: "checkbox", path: "content.loop" }),
                field({ key: "videoMuted", label: "Silenciado", type: "checkbox", path: "content.muted" }),
                field({ key: "videoControls", label: "Mostrar controles", type: "checkbox", path: "content.controls" }),
                field({ key: "videoPlaysInline", label: "Reproducir dentro del móvil", type: "checkbox", path: "content.playsInline" }),
                field({
                    key: "videoLoading",
                    label: "Carga",
                    type: "select",
                    path: "content.loading",
                    options: [["lazy", "Diferida"], ["eager", "Inmediata"]],
                }),
            ],
        }),
        actionGroup({
            id: "video-files",
            title: "Archivo local",
            actions: [
                action({
                    id: "upload-video-file",
                    label: "Subir video desde mis archivos",
                    handler: async ({ inspector, uploadService, state, node }) => {
                        if (!uploadService) {
                            inspector.onStatus?.("La carga de archivos no está configurada.");
                            return;
                        }

                        const input = document.createElement("input");
                        input.type = "file";
                        input.accept = "video/mp4,video/webm,video/ogg,video/quicktime,video/x-m4v,.mp4,.webm,.ogv,.ogg,.mov,.m4v";
                        input.hidden = true;
                        document.body.append(input);

                        input.addEventListener("change", async () => {
                            try {
                                const file = input.files?.[0];
                                if (!file) return;
                                const asset = await uploadService.importFile(file);
                                const current = state.getNode(node.id);
                                if (!current) return;
                                state.updateNode(current.id, {
                                    content: {
                                        ...(current.content || {}),
                                        sourceType: "library",
                                        assetId: asset.id,
                                        source: asset.url,
                                        title: current.content?.title || asset.name,
                                    },
                                });
                                inspector.renderer.update(state.document);
                                inspector.canvas.refreshAfterRender();
                                inspector.canvas.select(current.id);
                                inspector.refresh();
                                inspector.onStatus?.(`${asset.name} cargado y asignado al video`);
                            } catch (error) {
                                inspector.onStatus?.(error?.message || "No se pudo cargar el video.");
                            } finally {
                                input.remove();
                            }
                        }, { once: true });

                        input.click();
                    },
                }),
            ],
        }),
        group({
            id: "video-appearance",
            title: "Apariencia",
            fields: [
                field({ key: "videoRadius", label: "Radio", type: "number", path: "style.borderRadius", min: 0, max: 300, step: 1, unit: "px" }),
                field({ key: "videoBorderWidth", label: "Grosor del borde", type: "number", path: "style.borderWidth", min: 0, max: 30, step: 1, unit: "px" }),
                field({ key: "videoBorderColor", label: "Color del borde", type: "color", path: "style.borderColor" }),
                field({ key: "videoBackground", label: "Fondo", type: "color", path: "style.backgroundColor" }),
                field({ key: "videoShadow", label: "Sombra CSS", type: "text", path: "style.boxShadow", placeholder: "0 12px 32px rgba(0,0,0,.18)" }),
            ],
        }),
    ];
}

function libraryVideoOptions(assets) {
    const videos = assets?.list?.({ type: VIDEO_ASSET_TYPE }) || [];
    return [
        ["", videos.length ? "Selecciona un video" : "No hay videos en la biblioteca"],
        ...videos.map((asset) => [asset.id, `${asset.name} · ${asset.collection || "Biblioteca"}`]),
    ];
}

import { field, group } from "../controls.js";

export function videoPanel() {
    return [
        group({
            id: "video-content",
            title: "Video / YouTube",
            description: "Usa una URL de YouTube o una URL directa MP4/WebM.",
            fields: [
                field({
                    key: "videoSourceType",
                    label: "Tipo de fuente",
                    type: "select",
                    path: "content.sourceType",
                    options: [
                        ["youtube", "YouTube"],
                        ["direct", "Video directo"],
                        ["auto", "Detectar automáticamente"],
                    ],
                }),
                field({
                    key: "videoSource",
                    label: "URL o fuente",
                    type: "textarea",
                    path: "content.source",
                    placeholder: "https://www.youtube.com/watch?v=... o https://.../video.mp4",
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

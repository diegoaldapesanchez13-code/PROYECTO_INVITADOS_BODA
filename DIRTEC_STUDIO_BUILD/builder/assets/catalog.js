
import {
    ASSET_TYPES,
} from "./asset_manager.js";

export function createStarterAssetCatalog() {
    return [
        {
            id: "bg-olive-watercolor",
            type: ASSET_TYPES.BACKGROUND,
            name: "Acuarela olivo",
            category: "Fondos",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600">
                    <defs>
                        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0" stop-color="#f7f1e5"/>
                            <stop offset=".48" stop-color="#e8e1d0"/>
                            <stop offset="1" stop-color="#a5ad86"/>
                        </linearGradient>
                        <filter id="blur">
                            <feGaussianBlur stdDeviation="38"/>
                        </filter>
                    </defs>
                    <rect width="1200" height="1600" fill="url(#g)"/>
                    <g filter="url(#blur)" opacity=".42">
                        <ellipse cx="180" cy="220" rx="300" ry="210" fill="#7d895f"/>
                        <ellipse cx="1030" cy="1380" rx="360" ry="280" fill="#5d6b49"/>
                        <ellipse cx="890" cy="330" rx="240" ry="180" fill="#c9b77a"/>
                    </g>
                </svg>
            `),
            tags: ["olivo", "acuarela", "elegante"],
            metadata: {
                aspectRatio: .75,
            },
        },
        {
            id: "bg-ivory-paper",
            type: ASSET_TYPES.TEXTURE,
            name: "Papel marfil",
            category: "Fondos",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600">
                    <filter id="noise">
                        <feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" stitchTiles="stitch"/>
                        <feColorMatrix values="1 0 0 0 .82  0 1 0 0 .78  0 0 1 0 .68  0 0 0 .16 0"/>
                    </filter>
                    <rect width="1200" height="1600" fill="#fbf8ef"/>
                    <rect width="1200" height="1600" filter="url(#noise)" opacity=".25"/>
                </svg>
            `),
            tags: ["papel", "marfil", "textura"],
            metadata: {
                aspectRatio: .75,
            },
        },
        {
            id: "dec-olive-corner-left",
            type: ASSET_TYPES.DECORATION,
            name: "Esquina olivo izquierda",
            category: "Decoraciones",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="650" height="650" viewBox="0 0 650 650">
                    <g fill="none" stroke-linecap="round">
                        <path d="M44 610C120 430 230 260 520 70" stroke="#586647" stroke-width="11"/>
                        <path d="M100 505C180 475 230 405 256 340" stroke="#667655" stroke-width="7"/>
                        <path d="M205 360C305 350 376 280 414 210" stroke="#667655" stroke-width="7"/>
                    </g>
                    <g fill="#75845e">
                        <ellipse cx="118" cy="500" rx="34" ry="72" transform="rotate(-52 118 500)"/>
                        <ellipse cx="175" cy="430" rx="32" ry="68" transform="rotate(-45 175 430)"/>
                        <ellipse cx="250" cy="350" rx="31" ry="66" transform="rotate(-38 250 350)"/>
                        <ellipse cx="324" cy="280" rx="28" ry="62" transform="rotate(-34 324 280)"/>
                        <ellipse cx="408" cy="205" rx="26" ry="58" transform="rotate(-30 408 205)"/>
                        <ellipse cx="487" cy="132" rx="24" ry="54" transform="rotate(-28 487 132)"/>
                    </g>
                    <g fill="#a7ae70">
                        <circle cx="155" cy="464" r="18"/>
                        <circle cx="290" cy="321" r="17"/>
                        <circle cx="447" cy="171" r="16"/>
                    </g>
                </svg>
            `),
            tags: ["rama", "hojas", "esquina"],
            metadata: {
                transparent: true,
                aspectRatio: 1,
            },
        },
        {
            id: "dec-olive-corner-right",
            type: ASSET_TYPES.DECORATION,
            name: "Esquina olivo derecha",
            category: "Decoraciones",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="650" height="650" viewBox="0 0 650 650">
                    <g transform="translate(650 0) scale(-1 1)">
                        <g fill="none" stroke-linecap="round">
                            <path d="M44 610C120 430 230 260 520 70" stroke="#586647" stroke-width="11"/>
                            <path d="M100 505C180 475 230 405 256 340" stroke="#667655" stroke-width="7"/>
                            <path d="M205 360C305 350 376 280 414 210" stroke="#667655" stroke-width="7"/>
                        </g>
                        <g fill="#75845e">
                            <ellipse cx="118" cy="500" rx="34" ry="72" transform="rotate(-52 118 500)"/>
                            <ellipse cx="175" cy="430" rx="32" ry="68" transform="rotate(-45 175 430)"/>
                            <ellipse cx="250" cy="350" rx="31" ry="66" transform="rotate(-38 250 350)"/>
                            <ellipse cx="324" cy="280" rx="28" ry="62" transform="rotate(-34 324 280)"/>
                            <ellipse cx="408" cy="205" rx="26" ry="58" transform="rotate(-30 408 205)"/>
                            <ellipse cx="487" cy="132" rx="24" ry="54" transform="rotate(-28 487 132)"/>
                        </g>
                    </g>
                </svg>
            `),
            tags: ["rama", "hojas", "esquina"],
            metadata: {
                transparent: true,
                aspectRatio: 1,
            },
        },
        {
            id: "dec-gold-frame",
            type: ASSET_TYPES.DECORATION,
            name: "Marco dorado fino",
            category: "Marcos",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000" viewBox="0 0 800 1000">
                    <rect x="34" y="34" width="732" height="932" rx="30" fill="none" stroke="#b79a4d" stroke-width="7"/>
                    <rect x="52" y="52" width="696" height="896" rx="24" fill="none" stroke="#d5c17c" stroke-width="2"/>
                    <g fill="#b79a4d">
                        <path d="M400 20l12 19 23 4-17 16 4 23-22-11-22 11 4-23-17-16 23-4z"/>
                        <path d="M400 980l12-19 23-4-17-16 4-23-22 11-22-11 4 23-17 16 23 4z"/>
                    </g>
                </svg>
            `),
            tags: ["marco", "dorado", "borde"],
            metadata: {
                transparent: true,
                aspectRatio: .8,
            },
        },
        {
            id: "dec-gold-divider",
            type: ASSET_TYPES.DECORATION,
            name: "Separador dorado",
            category: "Decoraciones",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="900" height="120" viewBox="0 0 900 120">
                    <path d="M30 60h330M540 60h330" stroke="#b79a4d" stroke-width="3"/>
                    <path d="M450 15l45 45-45 45-45-45z" fill="none" stroke="#b79a4d" stroke-width="4"/>
                    <circle cx="450" cy="60" r="11" fill="#b79a4d"/>
                </svg>
            `),
            tags: ["separador", "dorado", "ornamento"],
            metadata: {
                transparent: true,
                aspectRatio: 7.5,
            },
        },
        {
            id: "img-church-placeholder",
            type: ASSET_TYPES.IMAGE,
            name: "Fotografía arquitectura",
            category: "Fotografías",
            collection: "Olivo Premium",
            url: svgDataUri(`
                <svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700">
                    <defs>
                        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0" stop-color="#bfcbd2"/>
                            <stop offset="1" stop-color="#f3e8d4"/>
                        </linearGradient>
                    </defs>
                    <rect width="1000" height="700" fill="url(#sky)"/>
                    <rect y="530" width="1000" height="170" fill="#7d886e"/>
                    <g fill="#c9bca5" stroke="#6c6256" stroke-width="7">
                        <rect x="270" y="230" width="460" height="330"/>
                        <rect x="205" y="315" width="110" height="245"/>
                        <rect x="685" y="315" width="110" height="245"/>
                        <path d="M270 230l230-155 230 155z"/>
                        <path d="M205 315l55-120 55 120z"/>
                        <path d="M685 315l55-120 55 120z"/>
                    </g>
                    <g fill="#5b5148">
                        <rect x="455" y="370" width="90" height="190" rx="45"/>
                        <circle cx="500" cy="255" r="58"/>
                    </g>
                </svg>
            `),
            tags: ["iglesia", "arquitectura", "foto"],
            metadata: {
                aspectRatio: 1.428,
            },
        },
    ];
}

function svgDataUri(svg) {
    const normalized = svg
        .replace(/\s{2,}/g, " ")
        .trim();

    return "data:image/svg+xml;charset=UTF-8,"
        + encodeURIComponent(normalized);
}

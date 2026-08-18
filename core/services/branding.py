import re
from dataclasses import dataclass, asdict


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class BrandContext:
    product_name: str = "DIRTEC Event Studio"
    company_name: str = ""
    logo_url: str = ""
    hero_url: str = ""
    primary: str = "#1F2937"
    secondary: str = "#64748B"
    accent: str = "#2563EB"

    def as_dict(self):
        return asdict(self)


def _safe_hex(value, fallback):
    if isinstance(value, str):
        value = value.strip()
        if _HEX_COLOR.fullmatch(value):
            return value.upper()
    return fallback


def _pick(mapping, *keys):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _file_url(field):
    if not field:
        return ""
    try:
        return field.url
    except (ValueError, AttributeError):
        return ""


def get_brand_context(empresa=None):
    """
    Presentation-only brand projection.

    K9.R1A intentionally does not add new database fields. It consumes the
    existing EmpresaSuscriptora.logotipo / colores_marca contract and provides
    stable keys that future app-shell templates can depend on.

    R13 may extend the storage model without forcing template rewrites.
    """
    defaults = BrandContext()
    if empresa is None:
        return defaults.as_dict()

    colores = empresa.colores_marca if isinstance(empresa.colores_marca, dict) else {}

    primary = _safe_hex(
        _pick(colores, "primary", "principal", "color_principal"),
        defaults.primary,
    )
    secondary = _safe_hex(
        _pick(colores, "secondary", "secundario", "color_secundario"),
        defaults.secondary,
    )
    accent = _safe_hex(
        _pick(colores, "accent", "acento", "color_acento"),
        defaults.accent,
    )

    return BrandContext(
        company_name=(empresa.nombre_comercial or "").strip(),
        logo_url=_file_url(empresa.logotipo),
        primary=primary,
        secondary=secondary,
        accent=accent,
    ).as_dict()

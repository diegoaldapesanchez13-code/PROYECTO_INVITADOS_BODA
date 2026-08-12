# K.4.3 — Clients, Team and Providers UX

## Product separation

### Clients
External portal identities. They are not internal company staff.

### Team
Internal tenant accounts only:
- ADMIN_EMPRESA
- VENTAS
- WEDDING_PLANNER

CLIENTE and PROVEEDOR cannot be selected from Team role editing.

### Providers
A first-class company module, separate from Catalogs.

Provider data is split visually into:
1. commercial/operational contact;
2. portal identity.

## Directory-first UX

Clients, Team and Providers open on searchable directories.
Create forms are secondary actions.
Edit forms stay collapsed per record.

## Catalogs

Catalogs now represent reusable company resources:
- Sedes
- Paquetes

Providers are not a catalog subpanel anymore.

## Protected behavior

K.1/K.2 tenant isolation stays unchanged.
K.3 username/email/phone login stays unchanged.
Django Admin stays DIRTEC-only.
No model or migration change.

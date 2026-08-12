# K.3 — Identity & Login

## Login identifier

A tenant user can authenticate with:
- username
- email
- registered phone

Password remains Django's protected password hash. Existing passwords are never
shown back to administrators.

## Identity vs business contact

Client / Planner identity:
- username
- email
- phone
- temporary/new password
- active state

Provider keeps business contact data in `Proveedor`, and a separate portal
identity can be linked with:
- username
- email
- phone
- temporary/new password

## Role home

CLIENTE and PROVEEDOR are external portal roles and never enter the company
backoffice through the central role redirect.

A CLIENTE with zero assigned events still enters the client portal, where the
empty state is shown.

## Django Admin

K.3 does not change the K.1/K.2 rule: Django Admin is DIRTEC-only.

# K.1 + K.2 — Tenant Context & Authorization

## Product contract

DIRTEC:
- can switch tenant deliberately;
- manages companies/plans/subscriptions;
- is the only role allowed into Django Admin.

Tenant users:
- never derive tenant from GET/POST;
- get tenant from authenticated membership/client/provider relationships;
- fail closed when associated with multiple active companies.

Event selection is still valid inside the fixed tenant.

## Central permission matrix

The first matrix covers:
- company users/catalogs;
- event create/view/edit;
- guests/tables/builder/operations;
- client portal/approvals;
- provider portal/service updates;
- Django Admin.

Existing company catalog/user helpers now delegate to the matrix.

## No migration

This phase changes architecture and authorization only.

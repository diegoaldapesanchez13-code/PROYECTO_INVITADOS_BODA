# K.8.1.1 — Collaboration Auth / Session Hotfix

## Reported bug

`cliente_crear_solicitud` queried:

`EventoBoda.objects.filter(clientes=request.user)`

This could raise a raw 404 after a Client page had already rendered if the
session changed in another browser tab, or if the POST role/context no longer
matched the page.

All tabs in the same browser profile share the Django session cookie. Logging
in as Planner or Provider in another tab changes the session for the old
Client tab too.

## Fix

- Client collaboration writes now use one client-event authorization contract.
- Stale/wrong-role Client POST redirects safely to role routing with a message.
- It no longer exposes a DEBUG 404 for this case.
- Provider direct collaboration access additionally requires active Provider
  role permission.
- Provider reassignment is blocked once an expediente has a Provider, avoiding
  leakage of previous provider conversation/quotes to a replacement Provider.
- Collaboration events now generate in-app notifications between roles.
- Included-in-package proposals are available in Planner UI without requiring
  an accepted Provider quote.

## Testing multiple roles

Use separate browser profiles/incognito sessions for Client, Planner and
Provider. Different tabs in the same browser profile are not separate logins.

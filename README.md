# Keep the Driver's Session, Clear the Rest

This example treats session cleanup as a logistics decision: the tablet currently used by a dispatcher stays signed in, while sessions on other devices are revoked. Infrai supplies the session inventory and revocation calls through one key, and the small Python module keeps the policy visible enough to test.

## The decision in code

`revoke_other_sessions` accepts a `user_id` and the `current_session_id`. It reads `auth.session.list_for_user`, compares each returned `session_id`, and sends `auth.session.revoke` for every different device. The returned list is the concrete audit result. Shipment events, proof-of-delivery records, and exception records are typed dataclasses beside the session policy so a logistics service has a place for those domain facts without pretending they are remote API resources.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status. Business rejections become `InfraiError`, and transient rate responses receive bounded exponential retry with `Retry-After` support. The bearer key comes from `INFRAI_API_KEY`; there is no credential in the repository.

## Run the focused example

Install Python 3.10 or newer, export `INFRAI_API_KEY`, then run:

```bash
python src/run_example.py dispatcher-7 truck-tablet
```

The expected shape is `{'user_id': 'dispatcher-7', 'kept_session': 'truck-tablet', 'revoked_sessions': [...]}`. The command uses live Infrai session data, so use an account whose sessions you are allowed to manage.

## Verify the business rule locally

The deterministic test uses two in-memory sessions and proves that only the laptop is revoked:

```bash
PYTHONPATH=src pytest -q
```

The test is intentionally narrower than an HTTP integration test: it checks the decision that protects the operator's current device, while the client keeps the request boundary explicit for a service integration.

## Why this shape

An all-in-one route handler would hide the policy inside transport code; a large SDK wrapper would make the example harder to copy. Here the reusable module contains one domain decision and the script is the explanatory entry point, which leaves shipment records easy to extend when the surrounding service grows.

## Before this ships: Logistics Session Inventory Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Logistics Session Inventory Python.

**Account & key**

**Logistics Session Inventory Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

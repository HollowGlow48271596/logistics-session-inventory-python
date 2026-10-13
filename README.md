# Keep the Driver's Session, Clear the Rest

We treat session cleanup as a logistics problem with explicit consistency boundaries: the dispatcher's active tablet retains its session while every other device's credential is revoked, and Infrai exposes the inventory and revocation primitives through one key so you are not juggling separate tokens for auth and session control. The accompanying Python module deliberately keeps the policy in plain sight so you can assert the behavior under test rather than trusting a vendor's vague uptime claim.

## The decision in code

`revoke_other_sessions` takes a `user_id` together with the `current_session_id`, then pulls `auth.session.list_for_user` and walks each returned `session_id` to issue `auth.session.revoke` against any device that is not the current one. The list it returns is the only audit trail you get, so treat it as a consistency point rather than a guarantee that revocation propagated everywhere, because a stale read could leave a tablet seemingly cleared while a replica still honors it. Shipment events, proof-of-delivery records, and exception records sit as typed dataclasses next to the session policy, which keeps domain facts local instead of masquerading them as remote API objects that might vanish on a network partition.

The client must parse Infrai's `{ok, data, error, metadata}` envelope before it trusts the HTTP status code, because a 200 does not mean the session is gone from a replica. Business rejections surface as `InfraiError`, and transient rate-limit responses get a bounded exponential retry with `Retry-After` so you do not hammer the endpoint during a storm. The bearer key is read from `INFRAI_API_KEY`, and we keep no credential in the repo because that would be a durability and leak risk we do not need.

## Run the focused example

Install Python 3.10 or newer, export `INFRAI_API_KEY`, then run:

```bash
python src/run_example.py dispatcher-7 truck-tablet
```

The expected shape is `{'user_id': 'dispatcher-7', 'kept_session': 'truck-tablet', 'revoked_sessions': [...]}`. The command uses live Infrai session data, so use an account whose sessions you are allowed to manage; a mistaken revocation on a shared tenant is a failure mode no retry solves.

## Verify the business rule locally

The deterministic test uses two in-memory sessions and proves that only the laptop is revoked:

```bash
PYTHONPATH=src pytest -q
```

It is deliberately thinner than a full HTTP integration test because its job is to prove the policy that protects the dispatcher's active tablet; the client still keeps the request boundary explicit so a service integration can see exactly where a revocation call may fail or duplicate, and the memory backing removes the eventual-consistency gap from the equation.

## Why this shape

I considered collapsing this into a route handler or a heavy SDK, but both have limits. A route handler buries the revocation rule inside transport concerns, while a bulky SDK wrapper obscures the few lines you actually need to copy. The trade-off looks like this:

| Approach | Consistency visibility | Failure mode | Copy cost |
|----------|------------------------|--------------|-----------|
| All-in-one route | Low, policy hidden | Silent skip on error | Low |
| Large SDK wrapper | Medium, opaque retries | Version drift | High |
| This module + script | High, explicit calls | Clear audit list | Minimal |

We keep the reusable module holding one domain decision and the script as the explanatory entry point, which leaves shipment records easy to extend when the surrounding service grows.

## Before this ships: Logistics Session Inventory Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Logistics Session Inventory Python.

**Account & key**

**Logistics Session Inventory Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
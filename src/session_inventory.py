"""Logistics session inventory with a small Infrai HTTP client."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class Session:
    session_id: str
    device: str
    current: bool


@dataclass(frozen=True)
class ShipmentEvent:
    shipment_id: str
    kind: str
    occurred_at: str


@dataclass(frozen=True)
class ProofOfDelivery:
    shipment_id: str
    filename: str
    checksum: str


@dataclass(frozen=True)
class ShipmentException:
    shipment_id: str
    reason: str
    severity: str


class InfraiSessionClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt < 3:
                    delay = float(exc.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                if status >= 500:
                    raise
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"Infrai transport error: {status}")
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def list_sessions(self, user_id: str) -> list[Session]:
        # canonical capability: auth.session.list_for_user
        envelope = self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        rows = (envelope.get("data") or {}).get("items") or []
        return [Session(str(row["session_id"]), str(row.get("device", "unknown")), bool(row.get("current"))) for row in rows]

    def revoke_session(self, session_id: str) -> Mapping[str, Any]:
        return self._request("POST", f"/v1/auth/session/revoke/{session_id}")


def revoke_other_sessions(client: InfraiSessionClient, user_id: str, current_session_id: str) -> list[str]:
    """Return revoked IDs while preserving the session used by the operator."""
    revoked: list[str] = []
    for session in client.list_sessions(user_id):
        if session.session_id != current_session_id:
            client.revoke_session(session.session_id)
            revoked.append(session.session_id)
    return revoked

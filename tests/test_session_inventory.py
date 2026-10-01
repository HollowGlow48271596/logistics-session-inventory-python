from session_inventory import Session, revoke_other_sessions


class FakeClient:
    def __init__(self):
        self.revoked = []

    def list_sessions(self, user_id):
        return [Session("truck-tablet", "tablet", True), Session("dispatch-laptop", "laptop", False)]

    def revoke_session(self, session_id):
        self.revoked.append(session_id)


def test_sign_out_other_devices_keeps_current_session():
    client = FakeClient()
    result = revoke_other_sessions(client, "dispatcher-7", "truck-tablet")
    assert result == ["dispatch-laptop"]
    assert client.revoked == ["dispatch-laptop"]

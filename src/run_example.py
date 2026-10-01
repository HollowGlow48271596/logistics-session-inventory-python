"""Runnable logistics example: inventory a user's sessions and sign out other devices."""

import argparse

from session_inventory import InfraiSessionClient, revoke_other_sessions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id")
    parser.add_argument("current_session_id")
    args = parser.parse_args()
    client = InfraiSessionClient()
    revoked = revoke_other_sessions(client, args.user_id, args.current_session_id)
    print({"user_id": args.user_id, "kept_session": args.current_session_id, "revoked_sessions": revoked})


if __name__ == "__main__":
    main()

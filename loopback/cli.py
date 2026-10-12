import sys
from time import time

import requests


def main():
    cmd = ""

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

    code = 0

    if cmd == "send-message":
        code = send_message(sys.argv)
    else:
        code = 2

    if code == 2:
        print_usage()

    sys.exit(code)


def print_usage() -> None:
    print(
        "Usage: python -m cli\n"
        "  send-message <webhook_url> <chat_id> <text> [secret_token]"
    )


def send_message(argv: list[str]) -> int:
    if len(argv) < 5:
        return 2

    webhook_url = argv[2]
    chat_id = argv[3]
    text = argv[4]
    secret_token = argv[5] if len(argv) > 5 else None

    date = int(time())
    payload = {
        "update_id": date * 1000,
        "message": {
            "message_id": date * 1000,
            "chat": {
                "id": int(chat_id),
                "type": "private",
            },
            "from": {
                "id": 545,
                "username": "loopback",
                "first_name": "loopback",
            },
            "date": date,
            "text": text,
        }
    }
    headers = {
        "Content-Type": "application/json",
    }

    if secret_token:
        headers["X-Telegram-Bot-Api-Secret-Token"] = secret_token

    response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()

    print(response.text)

    return 0


if __name__ == "__main__":
    main()

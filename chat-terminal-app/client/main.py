from __future__ import annotations

import asyncio
import argparse

from .chat_handler import run_chat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal chat client")
    parser.add_argument(
        "--http",
        dest="http_base_url",
        default="http://127.0.0.1:8000",
        help="Base HTTP URL du serveur (par défaut: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--ws",
        dest="websocket_url",
        default="ws://127.0.0.1:8000/ws",
        help="URL WebSocket du serveur (par défaut: ws://127.0.0.1:8000/ws)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        "Connexion au serveur:\n"
        f"  HTTP: {args.http_base_url}\n"
        f"  WS:   {args.websocket_url}\n"
    )
    asyncio.run(run_chat(args.websocket_url, args.http_base_url))


if __name__ == "__main__":
    main()



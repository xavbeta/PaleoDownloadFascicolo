from __future__ import annotations

import argparse

from .client import PaleoClient
from .config import load_config


def download_fascicolo() -> None:
    config = load_config()
    client = PaleoClient(config)

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    documents = list(client.list_documents())
    if not documents:
        print("Nessun documento trovato per il fascicolo indicato.")
        return

    for document in documents:
        content = client.download_document(document)
        target = output_dir / document.filename
        target.write_bytes(content)
        print(f"Scaricato: {target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scarica i documenti di un fascicolo Paleo")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("download-fascicolo", help="Scarica tutti i documenti del fascicolo")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download-fascicolo":
        download_fascicolo()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

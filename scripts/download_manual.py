"""Download the Paleo WS manual PDF."""
from __future__ import annotations

from pathlib import Path
import requests

URL = (
    "https://paleodownload.regione.marche.it/"
    "PaleoWebService/PaleoWS_Versione5_AGID/ManualeTecnico/"
    "WSPaleoVer5.12-Agid.pdf"
)


def main() -> int:
    target = Path("docs") / "WSPaleoVer5.12-Agid.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(URL, timeout=60)
    response.raise_for_status()

    target.write_bytes(response.content)
    print(f"Manuale salvato in: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

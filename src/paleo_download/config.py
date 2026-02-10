from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class PaleoConfig:
    wsdl_url: str
    username: str
    password: str
    org_code: str
    fascicolo_id: str
    output_dir: Path
    list_method: Optional[str]
    download_method: Optional[str]
    service_name: Optional[str]
    port_name: Optional[str]


DEFAULT_ENV_FILE = ".env"
DEFAULT_WSDL_URL = (
    "https://paleows.regione.marche.it/"
    "PaleoWebServices2020R_Marche/PaleoWebService2.svc?singleWsdl"
)


def load_config(env_file: Optional[str] = None) -> PaleoConfig:
    load_dotenv(env_file or DEFAULT_ENV_FILE)

    def require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    return PaleoConfig(
        wsdl_url=os.getenv("PALEO_WSDL_URL", DEFAULT_WSDL_URL),
        username=require("PALEO_USERNAME"),
        password=require("PALEO_PASSWORD"),
        org_code=require("PALEO_ORG_CODE"),
        fascicolo_id=require("PALEO_FASCICOLO_ID"),
        output_dir=Path(os.getenv("PALEO_OUTPUT_DIR", "downloads")),
        list_method=os.getenv("PALEO_LIST_METHOD"),
        download_method=os.getenv("PALEO_DOWNLOAD_METHOD"),
        service_name=os.getenv("PALEO_SERVICE_NAME"),
        port_name=os.getenv("PALEO_PORT_NAME"),
    )

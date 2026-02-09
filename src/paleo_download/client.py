from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
import base64

import requests
from zeep import Client, Settings
from zeep.transports import Transport

from .config import PaleoConfig


@dataclass(frozen=True)
class DocumentReference:
    document_id: str
    filename: str
    mime_type: Optional[str] = None


class PaleoClient:
    def __init__(self, config: PaleoConfig) -> None:
        self._config = config
        session = requests.Session()
        session.auth = (config.username, config.password)
        transport = Transport(session=session, timeout=60)
        settings = Settings(strict=False, xml_huge_tree=True)
        self._client = Client(config.wsdl_url, transport=transport, settings=settings)

    def list_documents(self) -> Iterable[DocumentReference]:
        method = getattr(self._client.service, self._config.list_method)
        response = method(
            codiceAOO=self._config.org_code,
            fascicoloId=self._config.fascicolo_id,
        )
        return self._extract_documents(response)

    def download_document(self, document: DocumentReference) -> bytes:
        method = getattr(self._client.service, self._config.download_method)
        response = method(
            codiceAOO=self._config.org_code,
            documentoId=document.document_id,
        )
        return self._extract_file_content(response)

    @staticmethod
    def _extract_documents(response: object) -> Iterable[DocumentReference]:
        if response is None:
            return []

        documents = None
        if hasattr(response, "Documenti"):
            documents = response.Documenti
        elif isinstance(response, dict) and "Documenti" in response:
            documents = response["Documenti"]
        else:
            documents = response

        if documents is None:
            return []

        if not isinstance(documents, list):
            documents = [documents]

        output: list[DocumentReference] = []
        for item in documents:
            data = item
            if not isinstance(item, dict):
                data = getattr(item, "__dict__", {})

            document_id = str(data.get("Id") or data.get("DocumentId") or data.get("documentoId"))
            filename = (
                data.get("NomeFile")
                or data.get("FileName")
                or data.get("nomeFile")
                or f"documento_{document_id}.bin"
            )
            mime_type = data.get("MimeType") or data.get("mimeType")
            if document_id:
                output.append(DocumentReference(document_id=document_id, filename=filename, mime_type=mime_type))

        return output

    @staticmethod
    def _extract_file_content(response: object) -> bytes:
        if response is None:
            raise ValueError("Risposta vuota dal servizio di download documento")

        if isinstance(response, bytes):
            return response

        if isinstance(response, str):
            return base64.b64decode(response)

        payload = None
        if hasattr(response, "File"):
            payload = response.File
        elif isinstance(response, dict) and "File" in response:
            payload = response["File"]
        elif hasattr(response, "Contenuto"):
            payload = response.Contenuto
        elif isinstance(response, dict) and "Contenuto" in response:
            payload = response["Contenuto"]

        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            return base64.b64decode(payload)

        raise ValueError("Formato risposta non riconosciuto per il contenuto del documento")

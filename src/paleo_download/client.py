from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
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
    FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "codice_aoo": (
            "codiceAOO",
            "CodiceAOO",
            "aoo",
            "AOO",
            "codiceOrganizzazione",
            "CodiceOrganizzazione",
        ),
        "fascicolo_id": (
            "fascicoloId",
            "FascicoloId",
            "idFascicolo",
            "IdFascicolo",
            "identificativoFascicolo",
            "IdentificativoFascicolo",
        ),
        "documento_id": (
            "documentoId",
            "DocumentoId",
            "idDocumento",
            "IdDocumento",
            "idDocumentoPrimario",
            "IdDocumentoPrimario",
        ),
        "username": ("username", "userName", "utente", "UserName", "Utente"),
        "password": ("password", "pwd", "Password", "Pwd"),
    }

    def __init__(self, config: PaleoConfig) -> None:
        self._config = config
        session = requests.Session()
        session.auth = (config.username, config.password)
        transport = Transport(session=session, timeout=60)
        settings = Settings(strict=False, xml_huge_tree=True)
        self._client = Client(config.wsdl_url, transport=transport, settings=settings)
        self._service = self._resolve_service()
        self._list_method = self._resolve_operation(
            config.list_method,
            candidates=(
                "CercaDocumentiFascicolo",
                "CercaDocumentiFascicolo2",
                "GetDocumentiFascicolo",
                "GetDocumentiFascicolo2",
                "GetFascicoloDocumenti",
                "ListaDocumentiFascicolo",
            ),
            purpose="lista documenti",
        )
        self._download_method = self._resolve_operation(
            config.download_method,
            candidates=(
                "ScaricaDocumento",
                "ScaricaDocumento2",
                "DownloadDocumento",
                "GetDocumento",
                "GetFileDocumento",
                "DownloadFileDocumento",
            ),
            purpose="download documento",
        )

    def list_documents(self) -> Iterable[DocumentReference]:
        response = self._invoke_operation(
            self._list_method,
            {
                "codice_aoo": self._config.org_code,
                "fascicolo_id": self._config.fascicolo_id,
                "username": self._config.username,
                "password": self._config.password,
            },
            required_fields=("codice_aoo", "fascicolo_id"),
            purpose="lista documenti",
        )
        return self._extract_documents(response)

    def download_document(self, document: DocumentReference) -> bytes:
        response = self._invoke_operation(
            self._download_method,
            {
                "codice_aoo": self._config.org_code,
                "documento_id": document.document_id,
                "username": self._config.username,
                "password": self._config.password,
            },
            required_fields=("codice_aoo", "documento_id"),
            purpose="download documento",
        )
        return self._extract_file_content(response)

    def _resolve_service(self):
        if self._config.service_name and self._config.port_name:
            return self._client.bind(self._config.service_name, self._config.port_name)

        try:
            return self._client.service
        except ValueError as exc:
            raise ValueError(
                "Il WSDL non definisce un servizio di default. "
                "Imposta PALEO_SERVICE_NAME e PALEO_PORT_NAME per il binding."
            ) from exc

    def _resolve_operation(self, configured: Optional[str], candidates: Iterable[str], purpose: str) -> str:
        available = self._available_operations()
        if configured:
            if configured not in available:
                available_list = ", ".join(sorted(available))
                raise ValueError(
                    f"Metodo '{configured}' non trovato per {purpose}. "
                    f"Operazioni disponibili: {available_list}"
                )
            return configured

        for name in candidates:
            if name in available:
                return name

        available_list = ", ".join(sorted(available))
        raise ValueError(
            f"Impossibile determinare automaticamente il metodo per {purpose}. "
            f"Imposta PALEO_LIST_METHOD/PALEO_DOWNLOAD_METHOD. "
            f"Operazioni disponibili: {available_list}"
        )

    def _available_operations(self) -> set[str]:
        return set(self._service._binding._operations.keys())

    def _invoke_operation(
        self,
        method_name: str,
        values: dict[str, str],
        required_fields: tuple[str, ...],
        purpose: str,
    ):
        operation = self._service._binding._operations[method_name]
        payload = self._build_payload(operation, values, required_fields, purpose)
        method = getattr(self._service, method_name)
        return method(**payload)

    @classmethod
    def _build_payload(
        cls,
        operation,
        values: dict[str, str],
        required_fields: tuple[str, ...],
        purpose: str,
    ) -> dict[str, Any]:
        elements = cls._operation_elements(operation)
        if not elements:
            return values

        payload, matched = cls._map_values_to_elements(elements, values)
        if cls._has_required_fields(required_fields, matched):
            return payload

        nested = cls._try_nested_payload(elements, values)
        if nested:
            nested_payload, nested_matched = nested
            if cls._has_required_fields(required_fields, nested_matched):
                return nested_payload

        expected = ", ".join(name for name, _ in elements)
        missing = [field for field in required_fields if field not in matched]
        raise ValueError(
            f"Parametri non riconosciuti per {purpose}: {', '.join(missing)}. "
            f"Parametri attesi dal WSDL: {expected}"
        )

    @staticmethod
    def _operation_elements(operation) -> list[tuple[str, Any]]:
        body = getattr(operation.input, "body", None)
        body_type = getattr(body, "type", None)
        elements = getattr(body_type, "elements", None)
        return list(elements or [])

    @classmethod
    def _map_values_to_elements(
        cls,
        elements: Iterable[tuple[str, Any]],
        values: dict[str, str],
    ) -> tuple[dict[str, Any], set[str]]:
        element_names = [name for name, _ in elements]
        lowered = {name.lower(): name for name in element_names}
        payload: dict[str, Any] = {}
        matched: set[str] = set()

        for logical_key, actual_value in values.items():
            aliases = cls.FIELD_ALIASES.get(logical_key, ())
            for alias in aliases:
                matched_name = lowered.get(alias.lower())
                if matched_name:
                    payload[matched_name] = actual_value
                    matched.add(logical_key)
                    break

        return payload, matched

    @classmethod
    def _try_nested_payload(
        cls,
        elements: Iterable[tuple[str, Any]],
        values: dict[str, str],
    ) -> Optional[tuple[dict[str, Any], set[str]]]:
        best_payload: Optional[dict[str, Any]] = None
        best_matched: set[str] = set()

        for wrapper_name, wrapper in elements:
            wrapper_type = getattr(wrapper, "type", None)
            nested_elements = getattr(wrapper_type, "elements", None)
            if not nested_elements:
                continue

            nested_payload, nested_matched = cls._map_values_to_elements(nested_elements, values)
            if len(nested_matched) > len(best_matched):
                best_payload = {wrapper_name: nested_payload}
                best_matched = nested_matched

        if best_payload is None:
            return None
        return best_payload, best_matched

    @staticmethod
    def _has_required_fields(required_fields: tuple[str, ...], matched: set[str]) -> bool:
        return all(field in matched for field in required_fields)

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

            raw_id = data.get("Id") or data.get("DocumentId") or data.get("documentoId")
            if raw_id is None:
                continue
            document_id = str(raw_id)
            filename = (
                data.get("NomeFile")
                or data.get("FileName")
                or data.get("nomeFile")
                or f"documento_{document_id}.bin"
            )
            mime_type = data.get("MimeType") or data.get("mimeType")
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

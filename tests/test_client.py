import unittest

from paleo_download.client import PaleoClient


class _FakeType:
    def __init__(self, elements):
        self.elements = elements


class _FakeElement:
    def __init__(self, elements=None):
        self.type = _FakeType(elements or [])


class _FakeBody:
    def __init__(self, elements):
        self.type = _FakeType(elements)


class _FakeInput:
    def __init__(self, elements):
        self.body = _FakeBody(elements)


class _FakeOperation:
    def __init__(self, elements):
        self.input = _FakeInput(elements)


class PaleoClientPayloadTests(unittest.TestCase):
    def test_build_payload_direct_parameters(self):
        operation = _FakeOperation([
            ("CodiceAOO", _FakeElement()),
            ("FascicoloId", _FakeElement()),
        ])

        payload = PaleoClient._build_payload(
            operation,
            {
                "codice_aoo": "AOO1",
                "fascicolo_id": "F123",
                "username": "u",
                "password": "p",
            },
            required_fields=("codice_aoo", "fascicolo_id"),
            purpose="lista documenti",
        )

        self.assertEqual(payload, {"CodiceAOO": "AOO1", "FascicoloId": "F123"})

    def test_build_payload_nested_wrapper(self):
        wrapper = _FakeElement(
            elements=[
                ("codiceAOO", _FakeElement()),
                ("idDocumento", _FakeElement()),
                ("userName", _FakeElement()),
                ("password", _FakeElement()),
            ]
        )
        operation = _FakeOperation([("request", wrapper)])

        payload = PaleoClient._build_payload(
            operation,
            {
                "codice_aoo": "AOO1",
                "documento_id": "D7",
                "username": "u",
                "password": "p",
            },
            required_fields=("codice_aoo", "documento_id"),
            purpose="download documento",
        )

        self.assertEqual(
            payload,
            {
                "request": {
                    "codiceAOO": "AOO1",
                    "idDocumento": "D7",
                    "userName": "u",
                    "password": "p",
                }
            },
        )

    def test_extract_documents_skips_missing_id(self):
        docs = PaleoClient._extract_documents([
            {"NomeFile": "a.pdf"},
            {"Id": "42", "NomeFile": "b.pdf"},
        ])

        self.assertEqual(len(list(docs)), 1)
        doc = list(docs)[0]
        self.assertEqual(doc.document_id, "42")
        self.assertEqual(doc.filename, "b.pdf")


if __name__ == "__main__":
    unittest.main()

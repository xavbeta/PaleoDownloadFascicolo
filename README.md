# Paleo Download Fascicolo

Questa applicazione Python invoca i webservice SOAP del sistema di protocollo **Paleo** e scarica tutti i documenti contenuti in un fascicolo specifico.

## Requisiti

- Python 3.11+
- Dipendenze: `requests`, `zeep`

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## Configurazione

Copia `.env.example` in `.env` e completa i valori:

```bash
cp .env.example .env
```

Variabili principali:

- `PALEO_WSDL_URL`: URL del WSDL (es. endpoint Paleo WS Versione 5 AGID).
- `PALEO_USERNAME` / `PALEO_PASSWORD`: credenziali.
- `PALEO_ORG_CODE`: codice dell'ente/organizzazione.
- `PALEO_FASCICOLO_ID`: identificativo del fascicolo da scaricare.
- `PALEO_OUTPUT_DIR`: cartella di destinazione dei file.
- `PALEO_LIST_METHOD`: nome del metodo SOAP che restituisce i documenti del fascicolo.
- `PALEO_DOWNLOAD_METHOD`: nome del metodo SOAP che restituisce il contenuto del documento.

> Nota: i nomi dei metodi possono variare in base alla configurazione del servizio; consultare la documentazione del WS.

## Uso

```bash
PYTHONPATH=src python -m paleo_download.cli download-fascicolo
```

Il comando:

1. Recupera l'elenco documenti dal fascicolo.
2. Scarica ogni documento e lo salva nella cartella indicata.

## Documentazione ufficiale

Il manuale tecnico richiesto è disponibile all'URL:
`https://paleodownload.regione.marche.it/PaleoWebService/PaleoWS_Versione5_AGID/ManualeTecnico/WSPaleoVer5.12-Agid.pdf`

Se la rete non consente il download diretto, usare lo script `scripts/download_manual.py`.

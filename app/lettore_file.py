import csv
import json
from io import StringIO
from pathlib import Path


def leggi_csv(contenuto: str) -> list[dict]:
    """Legge un CSV e restituisce una lista di righe."""

    # DictReader interpreta la prima riga del CSV come intestazione
    # e restituisce ogni riga come dizionario.
    lettore = csv.DictReader(
        StringIO(contenuto)
    )

    # Verifica che il CSV contenga una riga di intestazione.
    if lettore.fieldnames is None:
        raise ValueError("Il file csv non contiene le intestazioni")

    return list(lettore)


def leggi_json(contenuto: str) -> list[dict]:
    """Legge un JSON e restituisce il suo contenuto."""

    try:
        # Converte la stringa JSON in una struttura dati Python.
        return json.loads(contenuto)
    except json.JSONDecodeError as errore:
        # Trasforma l'errore tecnico del parser JSON in un messaggio più chiaro.
        raise ValueError(
            "Il contenuto del file JSON non è valido."
        ) from errore


def leggi_file(nome_file: str, contenuto_file: bytes, ) -> list[dict]:
    """Sceglie il lettore corretto in base all'estensione del file."""

    # Evita di elaborare file caricati senza contenuto.
    if not contenuto_file:
        raise ValueError("Il file è vuoto")

    # Converte il contenuto binario del file in testo.
    contenuto = contenuto_file.decode("utf-8")

    # Estrae l'estensione del file e la normalizza in minuscolo.
    estensione = Path(nome_file).suffix.lower()

    # Se il file è CSV, usa il lettore CSV.
    if estensione == ".csv":
        return leggi_csv(contenuto)

    # Se il file è JSON, usa il lettore JSON.
    if estensione == ".json":
        return leggi_json(contenuto)

    # Tutti gli altri formati vengono rifiutati.
    raise ValueError("Formato non supportato. Usare un file CSV oppure JSON.")

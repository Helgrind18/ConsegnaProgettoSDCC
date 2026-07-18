import csv
import json
from io import StringIO
from pathlib import Path


def leggi_csv(contenuto: str) -> list[dict]:
    # Converte il contenuto di un file CSV in una lista di righe.

    lettore = csv.DictReader(StringIO(contenuto))

    if lettore.fieldnames is None:
        raise ValueError("Il file CSV non contiene le intestazioni.")

    return list(lettore)


def leggi_json(contenuto: str) -> list[dict]:
    # Converte il contenuto di un file JSON in una lista di dati.

    try:
        return json.loads(contenuto)
    except json.JSONDecodeError as errore:
        raise ValueError(
            "Il contenuto del file JSON non è valido."
        ) from errore


def leggi_file(
        nome_file: str,
        contenuto_file: bytes,
) -> list[dict]:
    # Legge un file CSV o JSON in base alla sua estensione

    if not contenuto_file:
        raise ValueError("Il file è vuoto.")

    try:
        contenuto = contenuto_file.decode("utf-8")
    except UnicodeDecodeError as errore:
        raise ValueError(
            "Il file non è codificato correttamente in UTF-8."
        ) from errore

    estensione = Path(nome_file).suffix.lower()

    if estensione == ".csv":
        return leggi_csv(contenuto)

    if estensione == ".json":
        return leggi_json(contenuto)

    raise ValueError(
        "Formato non supportato. Usare un file CSV oppure JSON."
    )

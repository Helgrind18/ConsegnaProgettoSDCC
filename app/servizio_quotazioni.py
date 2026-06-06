from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

import requests
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelli import (
    Portafoglio,
    QuotazioneCorrente,
    TitoloPosseduto,
)


load_dotenv()

URL_API_TWELVE_DATA = os.getenv(
    "URL_API_TWELVE_DATA",
    "https://api.twelvedata.com",
).rstrip("/")

TIMEOUT_SECONDI = 10


class ErroreConfigurazioneQuotazioni(Exception):
    """Errore sollevato quando manca la chiave API."""


class ErroreServizioQuotazioni(Exception):
    """Errore sollevato quando Twelve Data restituisce un errore."""


class ErrorePortafoglioNonTrovato(Exception):
    """Errore sollevato quando il portafoglio richiesto non esiste."""


def ottieni_chiave_api() -> str:
    """Restituisce la chiave API di Twelve Data."""

    chiave_api = os.getenv(
        "CHIAVE_API_TWELVE_DATA"
    )

    if not chiave_api:
        raise ErroreConfigurazioneQuotazioni(
            "La variabile CHIAVE_API_TWELVE_DATA non è configurata."
        )

    return chiave_api


def ottieni_prezzo_corrente(
    ticker: str,
) -> Decimal:
    """Recupera il prezzo corrente di un ticker da Twelve Data."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError(
            "Il ticker non può essere vuoto."
        )

    try:
        risposta = requests.get(
            f"{URL_API_TWELVE_DATA}/price",
            params={
                "symbol": ticker,
                "apikey": ottieni_chiave_api(),
            },
            timeout=TIMEOUT_SECONDI,
        )
    except requests.RequestException as errore:
        raise ErroreServizioQuotazioni(
            "Impossibile contattare Twelve Data."
        ) from errore

    try:
        contenuto = risposta.json()
    except ValueError as errore:
        raise ErroreServizioQuotazioni(
            "Twelve Data ha restituito una risposta non valida."
        ) from errore

    if not isinstance(
        contenuto,
        dict,
    ):
        raise ErroreServizioQuotazioni(
            "Twelve Data ha restituito una risposta non valida."
        )

    if not risposta.ok:
        messaggio = contenuto.get(
            "message",
            "Errore non specificato.",
        )

        raise ErroreServizioQuotazioni(
            f"Twelve Data ha restituito un errore: {messaggio}"
        )

    if "price" not in contenuto:
        raise ErroreServizioQuotazioni(
            f"Il prezzo del ticker '{ticker}' non è disponibile."
        )

    try:
        return Decimal(
            str(
                contenuto["price"]
            )
        )
    except InvalidOperation as errore:
        raise ErroreServizioQuotazioni(
            "Il prezzo restituito da Twelve Data non è numerico."
        ) from errore


def aggiorna_quotazione_corrente(
    sessione: Session,
    ticker: str,
) -> QuotazioneCorrente:
    """Recupera e salva il prezzo corrente di un ticker."""

    ticker = ticker.strip().upper()

    prezzo_corrente = ottieni_prezzo_corrente(
        ticker=ticker,
    )

    quotazione = sessione.get(
        QuotazioneCorrente,
        ticker,
    )

    if quotazione is None:
        quotazione = QuotazioneCorrente(
            ticker=ticker,
            prezzo_corrente=prezzo_corrente,
        )

        sessione.add(
            quotazione
        )
    else:
        quotazione.prezzo_corrente = prezzo_corrente

    quotazione.recuperata_il = datetime.now()

    sessione.flush()

    return quotazione


def aggiorna_quotazioni_portafoglio(
    sessione: Session,
    portafoglio_id: int,
) -> dict:
    """
    Aggiorna le quotazioni di tutti i titoli presenti nel portafoglio.

    Se una quotazione non può essere recuperata, la funzione termina
    immediatamente.
    """

    portafoglio = sessione.get(
        Portafoglio,
        portafoglio_id,
    )

    if portafoglio is None:
        raise ErrorePortafoglioNonTrovato(
            f"Il portafoglio con id={portafoglio_id} non esiste."
        )

    titoli = sessione.scalars(
        select(
            TitoloPosseduto
        )
        .where(
            TitoloPosseduto.portafoglio_id
            == portafoglio_id
        )
        .order_by(
            TitoloPosseduto.ticker
        )
    ).all()

    ticker_aggiornati = []

    for titolo in titoli:
        aggiorna_quotazione_corrente(
            sessione=sessione,
            ticker=titolo.ticker,
        )

        ticker_aggiornati.append(
            titolo.ticker
        )

    return {
        "portafoglio_id": portafoglio_id,
        "ticker_totali": len(
            titoli
        ),
        "ticker_aggiornati": ticker_aggiornati,
        "errori": [],
    }


def calcola_riepilogo_portafoglio(
    sessione: Session,
    portafoglio_id: int,
) -> dict:
    """Calcola il riepilogo finanziario di un portafoglio."""

    portafoglio = sessione.get(
        Portafoglio,
        portafoglio_id,
    )

    if portafoglio is None:
        raise ErrorePortafoglioNonTrovato(
            f"Il portafoglio con id={portafoglio_id} non esiste."
        )

    titoli = sessione.scalars(
        select(
            TitoloPosseduto
        )
        .where(
            TitoloPosseduto.portafoglio_id
            == portafoglio_id
        )
        .order_by(
            TitoloPosseduto.ticker
        )
    ).all()

    capitale_investito_totale = Decimal(
        "0"
    )

    valore_corrente_totale = Decimal(
        "0"
    )

    dettagli_titoli = []

    for titolo in titoli:
        quotazione = sessione.get(
            QuotazioneCorrente,
            titolo.ticker,
        )

        if quotazione is None:
            raise ErroreServizioQuotazioni(
                f"La quotazione del ticker '{titolo.ticker}' "
                "non è disponibile. Aggiornare prima le quotazioni."
            )

        capitale_investito = (
            titolo.quantita
            * titolo.prezzo_medio_acquisto
        )

        valore_corrente = (
            titolo.quantita
            * quotazione.prezzo_corrente
        )

        guadagno_perdita = (
            valore_corrente
            - capitale_investito
        )

        if capitale_investito == 0:
            variazione_percentuale = None
        else:
            variazione_percentuale = (
                guadagno_perdita
                / capitale_investito
                * Decimal("100")
            )

        capitale_investito_totale += (
            capitale_investito
        )

        valore_corrente_totale += (
            valore_corrente
        )

        dettagli_titoli.append(
            {
                "ticker": titolo.ticker,
                "quantita": str(
                    titolo.quantita
                ),
                "prezzo_medio_acquisto": str(
                    titolo.prezzo_medio_acquisto
                ),
                "capitale_investito": str(
                    capitale_investito
                ),
                "prezzo_corrente": str(
                    quotazione.prezzo_corrente
                ),
                "valore_corrente": str(
                    valore_corrente
                ),
                "guadagno_perdita": str(
                    guadagno_perdita
                ),
                "variazione_percentuale": (
                    str(
                        variazione_percentuale
                    )
                    if variazione_percentuale is not None
                    else None
                ),
                "recuperata_il": (
                    quotazione.recuperata_il.isoformat()
                ),
            }
        )

    guadagno_perdita_totale = (
        valore_corrente_totale
        - capitale_investito_totale
    )

    if capitale_investito_totale == 0:
        variazione_percentuale_totale = None
    else:
        variazione_percentuale_totale = (
            guadagno_perdita_totale
            / capitale_investito_totale
            * Decimal("100")
        )

    return {
        "portafoglio_id": portafoglio.id,
        "nome_portafoglio": portafoglio.nome,
        "riepilogo_completo": True,
        "quotazioni_mancanti": [],
        "capitale_investito_totale": str(
            capitale_investito_totale
        ),
        "capitale_investito_quotato": str(
            capitale_investito_totale
        ),
        "valore_corrente_totale": str(
            valore_corrente_totale
        ),
        "guadagno_perdita_totale": str(
            guadagno_perdita_totale
        ),
        "variazione_percentuale_totale": (
            str(
                variazione_percentuale_totale
            )
            if variazione_percentuale_totale is not None
            else None
        ),
        "titoli": dettagli_titoli,
    }
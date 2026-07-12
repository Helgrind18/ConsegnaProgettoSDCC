# Schemi Pydantic usati per validare i dati in ingresso prima dell'inserimento nel database.

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortafoglioInCreazione(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    # Nome obbligatorio del portafoglio, con lunghezza massima coerente con il modello database.
    nome: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ]

    # Descrizione facoltativa del portafoglio.
    descrizione: Annotated[
        str | None,
        Field(max_length=500),
    ] = None


class TitoloPossedutoInIngresso(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    # Simbolo del ticker, per esempio AAPL o MSFT.
    ticker: Annotated[
        str,
        Field(min_length=1, max_length=15),
    ]

    # Quantità posseduta: deve essere maggiore di zero.
    quantita: Annotated[
        Decimal,
        Field(gt=0, max_digits=18, decimal_places=6),
    ]

    # Prezzo medio di acquisto: non può essere negativo.
    prezzo_medio_acquisto: Annotated[
        Decimal,
        Field(ge=0, max_digits=18, decimal_places=6),
    ]

    # Data in cui il titolo è stato acquistato.
    data_acquisto: date

    # Settore economico associato al titolo.
    settore: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ]

    # Mercato o borsa di riferimento del titolo.
    mercato: Annotated[
        str,
        Field(min_length=1, max_length=50),
    ]

    @field_validator("ticker", "mercato", mode="before")
    @classmethod
    def normalizza_testo_maiuscolo(cls, valore: object) -> object:
        # Se il valore è testuale, viene normalizzato prima della validazione.
        if isinstance(valore, str):
            return valore.strip().upper()

        return valore

    @field_validator("data_acquisto")
    @classmethod
    def verifica_data_acquisto(cls, valore: date) -> date:
        # Non è consentito registrare acquisti con una data successiva a oggi.
        if valore > date.today():
            raise ValueError(
                "La data di acquisto non può essere successiva alla data odierna."
            )

        return valore

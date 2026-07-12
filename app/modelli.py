from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.connessione_database import BaseModelli


class Portafoglio(BaseModelli):
    # Nome della tabella associata al modello nel database.
    __tablename__ = "portafogli"

    # Identificativo univoco del portafoglio.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Nome obbligatorio assegnato al portafoglio.
    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Descrizione facoltativa del portafoglio.
    descrizione: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Data e ora di creazione del record, impostate automaticamente dal database.
    creato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # Data e ora dell'ultimo aggiornamento del record.
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relazione uno-a-molti: un portafoglio può contenere più titoli posseduti.
    # La cascata elimina anche i titoli associati quando viene eliminato il portafoglio.
    titoli_posseduti: Mapped[list[TitoloPosseduto]] = relationship(
        back_populates="portafoglio",
        cascade="all, delete-orphan",
    )


class TitoloPosseduto(BaseModelli):
    # Nome della tabella che contiene i titoli associati ai portafogli.
    __tablename__ = "titoli_posseduti"

    # Vincoli applicati direttamente alla tabella:
    # - evita duplicati dello stesso ticker nello stesso portafoglio;
    # - impone una quantità positiva;
    # - impedisce prezzi medi di acquisto negativi.
    __table_args__ = (
        UniqueConstraint(
            "portafoglio_id",
            "ticker",
            name="uq_titoli_posseduti_portafoglio_ticker",
        ),
        CheckConstraint(
            "quantita > 0",
            name="ck_titoli_posseduti_quantita_positiva",
        ),
        CheckConstraint(
            "prezzo_medio_acquisto >= 0",
            name="ck_titoli_posseduti_prezzo_non_negativo",
        ),
    )

    # Identificativo univoco del titolo posseduto.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Collegamento al portafoglio proprietario del titolo.
    # ondelete="CASCADE" mantiene coerente il database in caso di eliminazione del portafoglio.
    portafoglio_id: Mapped[int] = mapped_column(
        ForeignKey(
            "portafogli.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Simbolo del titolo finanziario, per esempio AAPL, MSFT o TSLA.
    ticker: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
    )

    # Quantità posseduta del titolo.
    quantita: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    # Prezzo medio di acquisto del titolo.
    prezzo_medio_acquisto: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    # Data di acquisto del titolo.
    data_acquisto: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Settore economico associato al titolo.
    settore: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Mercato o borsa di riferimento del titolo.
    mercato: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Data e ora di creazione del record.
    creato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # Data e ora dell'ultimo aggiornamento del record.
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relazione molti-a-uno: ogni titolo posseduto appartiene a un solo portafoglio.
    portafoglio: Mapped[Portafoglio] = relationship(
        back_populates="titoli_posseduti",
    )


class QuotazioneCorrente(BaseModelli):
    # Nome della tabella che memorizza le quotazioni correnti dei ticker.
    __tablename__ = "quotazioni_correnti"

    # Ticker del titolo.
    # È chiave primaria perché viene salvata una sola quotazione corrente per ticker.
    ticker: Mapped[str] = mapped_column(
        String(15),
        primary_key=True,
    )

    # Ultimo prezzo corrente recuperato per il ticker.
    prezzo_corrente: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    # Data e ora dell'ultimo recupero o aggiornamento della quotazione.
    recuperata_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

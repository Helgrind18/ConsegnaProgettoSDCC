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
    """Portafoglio personale contenente uno o più titoli."""

    __tablename__ = "portafogli"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    descrizione: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    creato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    titoli_posseduti: Mapped[list[TitoloPosseduto]] = relationship(
        back_populates="portafoglio",
        cascade="all, delete-orphan",
    )


class TitoloPosseduto(BaseModelli):
    """Titolo presente in un portafoglio."""

    __tablename__ = "titoli_posseduti"

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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    portafoglio_id: Mapped[int] = mapped_column(
        ForeignKey(
            "portafogli.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
    )

    quantita: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    prezzo_medio_acquisto: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    data_acquisto: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    settore: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    mercato: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    creato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    portafoglio: Mapped[Portafoglio] = relationship(
        back_populates="titoli_posseduti",
    )


class QuotazioneCorrente(BaseModelli):
    """Ultimo prezzo recuperato per un ticker."""

    __tablename__ = "quotazioni_correnti"

    ticker: Mapped[str] = mapped_column(
        String(15),
        primary_key=True,
    )

    prezzo_corrente: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    recuperata_il: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
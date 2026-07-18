from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelli import Portafoglio, TitoloPosseduto
from app.schemi import PortafoglioInCreazione, TitoloPossedutoInIngresso


class ErrorePortafoglioNonTrovato(Exception):
    """Il portafoglio richiesto non esiste."""


class ErroreTitoloNonTrovato(Exception):
    """Il titolo richiesto non esiste."""


class ErroreTickerGiaPresente(Exception):
    """Il ticker è già presente nel portafoglio."""


def crea_portafoglio(
        sessione: Session,
        nome: str,
        descrizione: str | None = None,
) -> Portafoglio:
    dati = PortafoglioInCreazione(
        nome=nome,
        descrizione=descrizione,
    )

    portafoglio = Portafoglio(
        nome=dati.nome,
        descrizione=dati.descrizione,
    )

    sessione.add(portafoglio)
    sessione.flush()

    return portafoglio


def aggiungi_titolo_manualmente(
        sessione: Session,
        portafoglio_id: int,
        dati: TitoloPossedutoInIngresso,
) -> TitoloPosseduto:
    _ottieni_portafoglio(sessione, portafoglio_id)
    _verifica_ticker_disponibile(
        sessione,
        portafoglio_id,
        dati.ticker,
    )

    titolo = TitoloPosseduto(
        portafoglio_id=portafoglio_id,
        ticker=dati.ticker,
        quantita=dati.quantita,
        prezzo_medio_acquisto=dati.prezzo_medio_acquisto,
        data_acquisto=dati.data_acquisto,
        settore=dati.settore,
        mercato=dati.mercato,
    )

    sessione.add(titolo)
    sessione.flush()

    return titolo


def modifica_titolo(
        sessione: Session,
        portafoglio_id: int,
        titolo_id: int,
        dati: TitoloPossedutoInIngresso,
) -> TitoloPosseduto:
    titolo = _ottieni_titolo(
        sessione,
        portafoglio_id,
        titolo_id,
    )

    # Il titolo corrente viene escluso, altrimenti il ticker
    # risulterebbe duplicato anche quando non viene modificato.
    _verifica_ticker_disponibile(
        sessione,
        portafoglio_id,
        dati.ticker,
        titolo_id_da_escludere=titolo_id,
    )

    titolo.ticker = dati.ticker
    titolo.quantita = dati.quantita
    titolo.prezzo_medio_acquisto = dati.prezzo_medio_acquisto
    titolo.data_acquisto = dati.data_acquisto
    titolo.settore = dati.settore
    titolo.mercato = dati.mercato

    sessione.flush()

    return titolo


def elimina_titolo(
        sessione: Session,
        portafoglio_id: int,
        titolo_id: int,
) -> None:
    titolo = _ottieni_titolo(
        sessione,
        portafoglio_id,
        titolo_id,
    )

    sessione.delete(titolo)
    sessione.flush()


def elimina_portafoglio(
        sessione: Session,
        portafoglio_id: int,
) -> None:
    portafoglio = _ottieni_portafoglio(
        sessione,
        portafoglio_id,
    )

    sessione.delete(portafoglio)
    sessione.flush()


def _ottieni_portafoglio(
        sessione: Session,
        portafoglio_id: int,
) -> Portafoglio:
    portafoglio = sessione.get(Portafoglio, portafoglio_id)

    if portafoglio is None:
        raise ErrorePortafoglioNonTrovato(
            f"Il portafoglio con id={portafoglio_id} non esiste."
        )

    return portafoglio


def _ottieni_titolo(
        sessione: Session,
        portafoglio_id: int,
        titolo_id: int,
) -> TitoloPosseduto:
    _ottieni_portafoglio(sessione, portafoglio_id)

    titolo = sessione.scalar(
        select(TitoloPosseduto).where(
            TitoloPosseduto.id == titolo_id,
            TitoloPosseduto.portafoglio_id == portafoglio_id,
        )
    )

    if titolo is None:
        raise ErroreTitoloNonTrovato(
            f"Il titolo con id={titolo_id} non esiste "
            f"nel portafoglio con id={portafoglio_id}."
        )

    return titolo


def _verifica_ticker_disponibile(
        sessione: Session,
        portafoglio_id: int,
        ticker: str,
        titolo_id_da_escludere: int | None = None,
) -> None:
    query = select(TitoloPosseduto).where(
        TitoloPosseduto.portafoglio_id == portafoglio_id,
        TitoloPosseduto.ticker == ticker,
    )

    if titolo_id_da_escludere is not None:
        query = query.where(
            TitoloPosseduto.id != titolo_id_da_escludere
        )

    titolo_esistente = sessione.scalar(query)

    if titolo_esistente is not None:
        raise ErroreTickerGiaPresente(
            f"Il ticker '{ticker}' è già presente nel portafoglio."
        )

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelli import Portafoglio, TitoloPosseduto
from app.schemi import (
    PortafoglioInCreazione,
    TitoloPossedutoInIngresso,
)


class ErrorePortafoglioNonTrovato(Exception):
    """Errore sollevato quando il portafoglio richiesto non esiste."""


class ErroreTitoloNonTrovato(Exception):
    """Errore sollevato quando il titolo richiesto non esiste."""


class ErroreTickerGiaPresente(Exception):
    """Errore sollevato quando un ticker è già presente nel portafoglio."""


def crea_portafoglio(
        sessione: Session,
        nome: str,
        descrizione: str | None = None,
) -> Portafoglio:
    # Valida i dati ricevuti prima di creare il modello
    dati_validati = PortafoglioInCreazione(
        nome=nome,
        descrizione=descrizione,
    )

    # Crea il portafoglio usando soltanto dati già validati
    portafoglio = Portafoglio(
        nome=dati_validati.nome,
        descrizione=dati_validati.descrizione,
    )

    sessione.add(portafoglio)
    sessione.flush()

    return portafoglio


def aggiungi_titolo_manualmente(
        sessione: Session,
        portafoglio_id: int,
        dati: TitoloPossedutoInIngresso,
) -> TitoloPosseduto:
    # Verifica che il portafoglio esista prima di aggiungere un titolo
    _ottieni_portafoglio(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
    )

    # Controlla che nello stesso portafoglio non esista già un titolo con lo stesso ticker
    _verifica_ticker_disponibile(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
        ticker=dati.ticker,
    )

    # Crea il titolo da associare al portafoglio.
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
    # Recupera il titolo assicurandosi che appartenga al portafoglio indicato
    titolo = _ottieni_titolo(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
        titolo_id=titolo_id,
    )

    # Controlla che il nuovo ticker non crei duplicati nello stesso portafoglio.
    _verifica_ticker_disponibile(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
        ticker=dati.ticker,
        titolo_id_da_escludere=titolo_id,
    )

    # Aggiorna i campi del titolo con i nuovi dati
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
    # Recupera il titolo da eliminare e verifica che appartenga al portafoglio indicato.
    titolo = _ottieni_titolo(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
        titolo_id=titolo_id,
    )

    # L'eliminazione viene eseguita sulla sessione corrente.
    sessione.delete(titolo)
    sessione.flush()


def elimina_portafoglio(
        sessione: Session,
        portafoglio_id: int,
) -> None:
    """Elimina un portafoglio e i dati collegati."""

    # Recupera il portafoglio prima di eliminarlo.
    portafoglio = _ottieni_portafoglio(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
    )

    # L'eliminazione del portafoglio comporta anche l'eliminazione dei dati collegati
    sessione.delete(portafoglio)
    sessione.flush()


def _ottieni_portafoglio(
        sessione: Session,
        portafoglio_id: int,
) -> Portafoglio:
    """Restituisce un portafoglio oppure solleva un errore."""

    portafoglio = sessione.get(
        Portafoglio,
        portafoglio_id,
    )

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
    """Restituisce un titolo appartenente al portafoglio indicato."""

    # Verifica prima che il portafoglio esista.
    _ottieni_portafoglio(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
    )

    # Recupera il titolo all'intero del portafoglio
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
    """Verifica che il ticker non sia già presente nel portafoglio."""

    # Costruisce una query per cercare eventuali titoli con lo stesso ticker.
    istruzione = select(TitoloPosseduto).where(
        TitoloPosseduto.portafoglio_id == portafoglio_id,
        TitoloPosseduto.ticker == ticker,
    )

    # Durante la modifica di un titolo, il titolo corrente viene escluso dal controllo.
    if titolo_id_da_escludere is not None:
        istruzione = istruzione.where(
            TitoloPosseduto.id != titolo_id_da_escludere
        )

    titolo_esistente = sessione.scalar(istruzione)

    if titolo_esistente is not None:
        raise ErroreTickerGiaPresente(
            f"Il ticker '{ticker}' è già presente nel portafoglio."
        )

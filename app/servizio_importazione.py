from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.lettore_file import leggi_file
from app.modelli import Portafoglio, TitoloPosseduto
from app.validazione_titoli import valida_titoli


class ErrorePortafoglioNonTrovato(Exception):
    """Il portafoglio richiesto non esiste."""


class ErroreFormatoFileNonSupportato(Exception):
    """Il formato del file non è supportato."""


def importa_file_in_portafoglio(
        sessione: Session,
        portafoglio_id: int,
        nome_file: str,
        contenuto_file: bytes,
) -> int:
    # Importa in un portafoglio i titoli contenuti in un file CSV o JSON.

    portafoglio = sessione.get(Portafoglio, portafoglio_id)

    if portafoglio is None:
        raise ErrorePortafoglioNonTrovato(
            f"Il portafoglio con id={portafoglio_id} non esiste."
        )

    estensione = Path(nome_file).suffix.lower()

    if estensione not in {".csv", ".json"}:
        raise ErroreFormatoFileNonSupportato(
            "Sono accettati soltanto file CSV oppure JSON."
        )

    righe = leggi_file(
        nome_file=nome_file,
        contenuto_file=contenuto_file,
    )

    # La validazione avviene prima del salvataggio, così non vengono
    # importati dati parziali se una delle righe contiene errori.
    titoli = valida_titoli(righe)

    verifica_ticker_gia_presenti(
        sessione=sessione,
        portafoglio_id=portafoglio_id,
        titoli=titoli,
    )

    titoli_da_salvare = [
        TitoloPosseduto(
            portafoglio_id=portafoglio_id,
            ticker=titolo.ticker,
            quantita=titolo.quantita,
            prezzo_medio_acquisto=titolo.prezzo_medio_acquisto,
            data_acquisto=titolo.data_acquisto,
            settore=titolo.settore,
            mercato=titolo.mercato,
        )
        for titolo in titoli
    ]

    sessione.add_all(titoli_da_salvare)
    sessione.flush()

    return len(titoli_da_salvare)


def verifica_ticker_gia_presenti(
        sessione: Session,
        portafoglio_id: int,
        titoli: list,
) -> None:
    # Controlla che i ticker non siano già presenti nel portafoglio.

    ticker_da_importare = [
        titolo.ticker
        for titolo in titoli
    ]

    ticker_esistenti = sessione.scalars(
        select(TitoloPosseduto.ticker).where(
            TitoloPosseduto.portafoglio_id == portafoglio_id,
            TitoloPosseduto.ticker.in_(ticker_da_importare),
        )
    ).all()

    if ticker_esistenti:
        raise ValueError(
            f"Il ticker '{ticker_esistenti[0]}' "
            "è già presente nel portafoglio."
        )

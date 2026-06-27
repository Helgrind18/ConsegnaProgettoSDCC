# Importa la funzione che cerca nel catalogo locale titoli appartenenti allo stesso settore.
from app.catalogo_titoli import trova_titoli_simili_per_settore
from app.servizio_analisi_ai import (
    ErroreConfigurazioneAnalisiAI,
    ErroreServizioAnalisiAI,
    genera_testo,
)


def genera_spiegazione_locale(
    ticker_riferimento: str,
    settore_riferimento: str,
    suggerimenti: list[dict[str, str]],
) -> str:
    """Genera una spiegazione locale quando Gemini non è disponibile."""

    # Costruisce una spiegazione semplice senza usare Gemini.
    # Questa funzione viene usata come fallback.
    righe = [
        (
            "I titoli proposti sono stati selezionati perché "
            f"appartengono allo stesso settore di {ticker_riferimento}: "
            f"{settore_riferimento}."
        ),
        "",
    ]

    # Elenca i titoli suggeriti usando solo dati presenti nel catalogo locale.
    for titolo in suggerimenti:
        righe.append(
            f"- {titolo['ticker']}: "
            f"{titolo['nome']} "
            f"({titolo['mercato']})."
        )

    righe.extend(
        [
            "",
            (
                "La spiegazione è stata generata localmente perché "
                "il servizio AI non è temporaneamente disponibile."
            ),
            (
                "I suggerimenti hanno finalità esplorative e non "
                "costituiscono consulenza finanziaria."
            ),
        ]
    )

    return "\n".join(
        righe
    )


def genera_suggerimenti_titoli_simili(
    ticker_riferimento: str,
    settore_riferimento: str,
    ticker_posseduti: list[str],
) -> dict[str, object]:
    """Suggerisce titoli dello stesso settore e genera una spiegazione."""

    # Normalizza i ticker già posseduti per escluderli dai suggerimenti.
    ticker_da_escludere = {
        ticker.upper()
        for ticker in ticker_posseduti
    }

    # Cerca titoli dello stesso settore nel catalogo dimostrativo locale.
    suggerimenti = trova_titoli_simili_per_settore(
        settore=settore_riferimento,
        ticker_da_escludere=ticker_da_escludere,
    )

    # Se non ci sono titoli simili disponibili, restituisce una risposta locale controllata.
    if not suggerimenti:
        return {
            "ticker_riferimento": ticker_riferimento,
            "settore": settore_riferimento,
            "suggerimenti": [],
            "spiegazione": (
                "Non sono disponibili altri titoli dello stesso settore "
                "nel catalogo dimostrativo."
            ),
            "origine_spiegazione": "locale",
        }

    # Prepara l'elenco dei suggerimenti da inserire nel prompt inviato a Gemini.
    elenco_suggerimenti = "\n".join(
        (
            f"- {titolo['ticker']}: "
            f"{titolo['nome']}, "
            f"settore {titolo['settore']}, "
            f"mercato {titolo['mercato']}."
        )
        for titolo in suggerimenti
    )

    # Prompt controllato: Gemini deve usare solo i dati forniti
    # e non deve produrre raccomandazioni finanziarie.
    richiesta = (
        "Scrivi una breve spiegazione in italiano dei titoli simili "
        "elencati di seguito.\n"
        "I titoli sono stati selezionati dall'applicazione perché "
        "appartengono allo stesso settore del titolo di riferimento.\n"
        "Usa esclusivamente ticker, nome, settore e mercato presenti "
        "nell'elenco fornito.\n"
        "Non aggiungere altri ticker.\n"
        "Non descrivere le attività svolte dalle aziende.\n"
        "Non aggiungere informazioni esterne o conoscenze generali.\n"
        "Non inventare dati finanziari, rendimenti o previsioni.\n"
        "Non fornire consigli di acquisto o vendita.\n"
        "Concludi specificando che i suggerimenti hanno finalità "
        "esplorative e non costituiscono consulenza finanziaria.\n\n"
        f"Titolo di riferimento: {ticker_riferimento}\n"
        f"Settore: {settore_riferimento}\n\n"
        "Titoli simili:\n"
        f"{elenco_suggerimenti}"
    )

    try:
        # Prima scelta: generare la spiegazione tramite Gemini.
        spiegazione = genera_testo(
            richiesta=richiesta
        )

        origine_spiegazione = "gemini"

    except (
        ErroreConfigurazioneAnalisiAI,
        ErroreServizioAnalisiAI,
    ):
        # Fallback: se Gemini non è configurato o non risponde,
        # viene generata una spiegazione locale.
        spiegazione = genera_spiegazione_locale(
            ticker_riferimento=ticker_riferimento,
            settore_riferimento=settore_riferimento,
            suggerimenti=suggerimenti,
        )

        origine_spiegazione = "locale"

    return {
        "ticker_riferimento": ticker_riferimento,
        "settore": settore_riferimento,
        "suggerimenti": suggerimenti,
        "spiegazione": spiegazione,
        "origine_spiegazione": origine_spiegazione,
    }

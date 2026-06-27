import logging
import os

from dotenv import load_dotenv
from google import genai


# Logger del modulo, usato per registrare eventuali errori nella chiamata a Gemini.
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente definite nel file .env, se presente.
# In questo modulo vengono usate soprattutto GEMINI_API_KEY e MODELLO_GEMINI.
load_dotenv()


class ErroreConfigurazioneAnalisiAI(Exception):
    """Errore sollevato quando manca una variabile di configurazione."""


class ErroreServizioAnalisiAI(Exception):
    """Errore sollevato quando Gemini non risponde correttamente."""


def ottieni_variabile_ambiente_obbligatoria(
    nome: str,
) -> str:
    """Restituisce una variabile d'ambiente obbligatoria."""

    # Legge il valore della variabile d'ambiente richiesta.
    valore = os.getenv(
        nome
    )

    # Se la variabile non è presente, viene sollevato un errore specifico
    # della configurazione del servizio AI.
    if not valore:
        raise ErroreConfigurazioneAnalisiAI(
            f"La variabile d'ambiente '{nome}' non è configurata."
        )

    return valore


def genera_testo(
    richiesta: str,
) -> str:
    """Invia una richiesta testuale a Gemini e restituisce la risposta."""

    # Recupera la chiave API necessaria per autenticarsi presso Gemini.
    chiave_api = ottieni_variabile_ambiente_obbligatoria(
        "GEMINI_API_KEY"
    )

    # Permette di configurare il modello da variabile d'ambiente.
    # Se non specificato, viene usato un modello predefinito.
    modello = os.getenv(
        "MODELLO_GEMINI",
        "gemini-2.5-flash-lite",
    )

    # Crea il client ufficiale per comunicare con Gemini.
    client = genai.Client(
        api_key=chiave_api
    )

    try:
        # Invia il prompt al modello e richiede la generazione del testo.
        risposta = client.models.generate_content(
            model=modello,
            contents=richiesta,
        )
    except Exception as errore:
        # L'errore tecnico viene registrato nei log,
        # ma verso il resto dell'applicazione viene esposto un errore controllato.
        logger.exception(
            "Errore durante la richiesta inviata a Gemini."
        )

        raise ErroreServizioAnalisiAI(
            "Non è stato possibile ottenere una risposta da Gemini."
        ) from errore

    # Anche una risposta priva di testo viene considerata non valida.
    if not risposta.text:
        raise ErroreServizioAnalisiAI(
            "Gemini non ha restituito alcun testo."
        )

    return risposta.text


def formatta_numero_locale(
    valore: str | float | int | None,
) -> str:
    """Formatta un numero secondo la convenzione italiana."""

    # Se il valore non è disponibile, restituisce una stringa descrittiva.
    if valore is None:
        return "non disponibile"

    # Converte il valore ricevuto in numero per poterlo formattare.
    numero = float(
        valore
    )

    # Applica la formattazione italiana:
    # punto per le migliaia e virgola per i decimali.
    return (
        f"{numero:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def genera_analisi_portafoglio_locale(
    riepilogo: dict,
) -> str:
    """Genera un report locale quando Gemini non è disponibile."""

    # Prime righe del report locale con i dati complessivi del portafoglio.
    righe = [
        (
            f'Il portafoglio "{riepilogo["nome_portafoglio"]}" '
            "presenta un capitale investito totale di "
            f'{formatta_numero_locale(
                riepilogo["capitale_investito_totale"]
            )} euro e un valore corrente totale di '
            f'{formatta_numero_locale(
                riepilogo["valore_corrente_totale"]
            )} euro.'
        ),
        (
            "Il guadagno o la perdita complessiva è pari a "
            f'{formatta_numero_locale(
                riepilogo["guadagno_perdita_totale"]
            )} euro, con una variazione percentuale del '
            f'{formatta_numero_locale(
                riepilogo["variazione_percentuale_totale"]
            )}%.'
        ),
    ]

    # Considera solo i titoli per cui è disponibile una variazione percentuale.
    titoli_con_variazione = [
        titolo
        for titolo in riepilogo["titoli"]
        if titolo["variazione_percentuale"] is not None
    ]

    if titoli_con_variazione:
        # Seleziona il titolo con la variazione percentuale più rilevante
        # in valore assoluto, quindi sia positiva sia negativa.
        titolo_piu_rilevante = max(
            titoli_con_variazione,
            key=lambda titolo: abs(
                float(
                    titolo["variazione_percentuale"]
                )
            ),
        )

        righe.extend(
            [
                "",
                (
                    "Il titolo con la variazione percentuale "
                    "più rilevante è "
                    f'{titolo_piu_rilevante["ticker"]}, '
                    "con una variazione del "
                    f'{formatta_numero_locale(
                        titolo_piu_rilevante[
                            "variazione_percentuale"
                        ]
                    )}%.'
                ),
            ]
        )

    # Chiusura del report locale con spiegazione del fallback
    # e disclaimer informativo.
    righe.extend(
        [
            "",
            (
                "L'analisi è stata generata localmente perché "
                "il servizio AI non è temporaneamente disponibile."
            ),
            (
                "Il testo ha finalità informative e non "
                "costituisce consulenza finanziaria."
            ),
        ]
    )

    return "\n".join(
        righe
    )


def genera_analisi_portafoglio(
    riepilogo: dict,
) -> str:
    """Genera una breve analisi descrittiva del portafoglio."""

    # Prepara una descrizione testuale sintetica dei singoli titoli,
    # che verrà inserita nel prompt inviato a Gemini.
    dettagli_titoli = []

    for titolo in riepilogo["titoli"]:
        dettagli_titoli.append(
            "- "
            f"{titolo['ticker']}: "
            f"capitale investito {titolo['capitale_investito']} euro, "
            f"valore corrente {titolo['valore_corrente']} euro, "
            f"guadagno o perdita {titolo['guadagno_perdita']} euro, "
            f"variazione {titolo['variazione_percentuale']}%."
        )

    elenco_titoli = "\n".join(
        dettagli_titoli
    )

    # Prompt inviato a Gemini.
    # Le istruzioni limitano l'output a un'analisi descrittiva,
    # evitando consigli di acquisto o vendita.
    richiesta = (
        "Genera una breve analisi descrittiva in italiano di questo "
        "portafoglio finanziario.\n"
        "Usa un linguaggio chiaro e sintetico.\n"
        "Usa la virgola come separatore decimale e il punto come "
        "separatore delle migliaia.\n"
        "Evidenzia l'andamento complessivo e il titolo con la variazione "
        "percentuale più rilevante.\n"
        "Non fornire consigli di acquisto o vendita.\n"
        "Concludi specificando che il testo ha finalità informative e "
        "non costituisce consulenza finanziaria.\n\n"
        f"Nome del portafoglio: {riepilogo['nome_portafoglio']}\n"
        f"Capitale investito totale: "
        f"{riepilogo['capitale_investito_totale']} euro\n"
        f"Valore corrente totale: "
        f"{riepilogo['valore_corrente_totale']} euro\n"
        f"Guadagno o perdita totale: "
        f"{riepilogo['guadagno_perdita_totale']} euro\n"
        f"Variazione percentuale totale: "
        f"{riepilogo['variazione_percentuale_totale']}%\n\n"
        "Dettaglio dei titoli:\n"
        f"{elenco_titoli}"
    )

    try:
        # Prima scelta: generazione dell'analisi tramite Gemini.
        return genera_testo(
            richiesta=richiesta
        )

    except (
        ErroreConfigurazioneAnalisiAI,
        ErroreServizioAnalisiAI,
    ):
        # Fallback: se Gemini non è configurato o non risponde,
        # viene generata un'analisi locale più semplice.
        return genera_analisi_portafoglio_locale(
            riepilogo=riepilogo
        )

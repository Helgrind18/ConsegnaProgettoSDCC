import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Carica le variabili d'ambiente definite nel file .env, se presente.
load_dotenv()


def ottieni_variabile_ambiente_obbligatoria(nome: str) -> str:
    #Restituisce una variabile d'ambiente oppure interrompe l'avvio.
    valore = os.getenv(nome)
    # Se la variabile richiesta non è presente, l'applicazione viene fermata evitando errori meno chiari in fase di connessione.
    if not valore:
        raise RuntimeError(
            f"La variabile d'ambiente obbligatoria '{nome}' non è definita."
        )

    return valore


# Costruisce l'URL di connessione al database MySQL usando le variabili d'ambiente.
# Utente, password e nome del database sono obbligatori.
# Host e porta hanno invece valori predefiniti utili per l'esecuzione locale.
url_database = URL.create(
    drivername="mysql+pymysql",
    username=ottieni_variabile_ambiente_obbligatoria("MYSQL_USER"),
    password=ottieni_variabile_ambiente_obbligatoria("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=ottieni_variabile_ambiente_obbligatoria("MYSQL_DATABASE"),
    query={"charset": "utf8mb4"},
)

# Crea il motore SQLAlchemy, cioè l'oggetto che gestisce le connessioni al database.
motore_database = create_engine(
    url_database,
    pool_pre_ping=True, # contorlla la validità delle connessioni prima di riutilizzarlo
)

# Crea le sessioni per le connessioni dei database, ogni sessione permette di eseguire query e operazioni sul database.
SessioneLocale = sessionmaker(
    bind=motore_database,
    autoflush=False,
    autocommit=False,
)


class BaseModelli(DeclarativeBase):
    """Classe di base condivisa da tutti i modelli SQLAlchemy."""
    pass

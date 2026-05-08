# MIST Webinar Quiz

App Streamlit per quiz live MIST con ruolo Relatore e Partecipante.

## Avvio locale

1. Installa dipendenze:
   pip install -r requirements.txt
2. Avvia:
   streamlit run fakenewsapp.py

## Deploy su Streamlit Community Cloud

1. Crea un nuovo repository GitHub.
2. Carica i file di questa cartella.
3. Apri https://share.streamlit.io e collega il repository.
4. Main file path: app.py
5. Python version: 3.11 (consigliata)

Nota: `fakenewsapp.py` e un alias di compatibilita che importa `app.py`.

## Password relatore (segreti)

Non salvare la password nel codice.

1. Locale: crea `.streamlit/secrets.toml` partendo da `.streamlit/secrets.toml.example`.
2. Streamlit Cloud: App -> Settings -> Secrets e inserisci:

   `PRESENTER_PASSWORD = "la-tua-password-forte"`

L'app legge prima `st.secrets["PRESENTER_PASSWORD"]`, poi la variabile ambiente `PRESENTER_PASSWORD`.

## Nota persistenza

Il database SQLite (mist_quiz.db) e locale all'istanza. Se l'app si riavvia, la sessione quiz si azzera.
Per webinar ad alta affidabilita, valuta un database remoto (Postgres/Supabase).

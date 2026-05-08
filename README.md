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
4. Main file path: fakenewsapp.py
5. Python version: 3.11 (consigliata)

## Nota persistenza

Il database SQLite (mist_quiz.db) e locale all'istanza. Se l'app si riavvia, la sessione quiz si azzera.
Per webinar ad alta affidabilita, valuta un database remoto (Postgres/Supabase).

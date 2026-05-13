# MIST – Fake News Quiz (Versione Asincrona)

Quiz individuale per autovalutazione sulla resistenza alla disinformazione.
Basato sul framework **MIST** (Maertens et al., 2024).

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

La app si apre su `http://localhost:8501`.

## Deploy su Streamlit Community Cloud

1. Carica il repository GitHub.
2. Vai a https://share.streamlit.io e collega il repository.
3. Main file path: `app.py`
4. Python version: 3.11 (consigliata)

L'app sarà disponibile come link pubblico da condividere con gli utenti.

## Utilizzo

1. L'utente inserisce il proprio nome
2. Risponde a 8 domande su notizie vere e false (5 secondi a domanda)
3. Vede i propri punteggi MIST e un'interpretazione personale
4. Può rivedere tutte le risposte in una tabella riepilogativa

Nessun database, nessun salvataggio: ogni sessione è indipendente.

## Architettura

- **Frontend**: Streamlit + `st.session_state` per memorizzare le risposte
- **Scoring**: Calcolo MIST-8 locale (Veracity Discernment, Real News Detection, Fake News Detection, Distrust, Naivité)
- **Deploy**: Stateless (ogni utente vede una sessione isolata)

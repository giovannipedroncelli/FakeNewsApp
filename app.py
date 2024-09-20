import random
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.let_it_rain import rain

# Configurazione della pagina
st.set_page_config(
    page_title="Test di riconoscimento fake news",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="auto",
)

# Titoli delle notizie (in italiano)
titoli = [
    "I funzionari governativi hanno manipolato i prezzi delle azioni per nascondere scandali.",
    "I media aziendali sono controllati dal complesso militare-industriale: le principali compagnie petrolifere possiedono i media e ne controllano l'agenda.",
    "Nuovo studio: le persone di sinistra mentono più facilmente per ottenere uno stipendio più alto.",
    "Il governo sta manipolando la percezione pubblica dell'ingegneria genetica per rendere le persone più inclini ad accettare tali tecniche.",
    "L'estremismo di sinistra causa più danni al mondo del terrorismo, afferma un rapporto dell'ONU.",
    "Alcuni vaccini sono carichi di sostanze chimiche e tossine pericolose.",
    "Nuovo studio: chiara relazione tra colore degli occhi e intelligenza.",
    "Il governo sta diffondendo consapevolmente malattie attraverso le onde radio e gli alimenti.",
    "Il virus Ebola è stato causato dai test nucleari degli Stati Uniti, afferma un nuovo studio.",
    "I funzionari governativi hanno illegalmente manipolato il clima per causare tempeste devastanti.",
    "Gli atteggiamenti verso l'UE sono ampiamente positivi, sia all'interno che all'esterno dell'Europa.",
    "Una persona su tre nel mondo non ha fiducia nelle ONG.",
    "Riflettendo il cambiamento demografico, 109 contee statunitensi sono diventate a maggioranza non-bianca dal 2000.",
    "Esperti di relazioni internazionali e pubblico statunitense concordano: l'America è meno rispettata a livello globale.",
    "Hyatt rimuoverà le bottigliette dai bagni degli hotel entro il 2021.",
    "Il re del Marocco nomina il capo del comitato per combattere povertà e disuguaglianza.",
    "I repubblicani sono divisi nelle opinioni sulla condotta di Trump, i democratici sono ampiamente critici.",
    "I democratici sono più favorevoli dei repubblicani alla spesa federale per la ricerca scientifica.",
    "Divario generazionale sul riscaldamento globale: i giovani americani sono i più preoccupati.",
    "Il sostegno degli Stati Uniti alla marijuana legale è stabile nell'ultimo anno."
]

# Risposte corrette (True per notizie reali, False per fake news)
risposte = [False, False, False, False, False, False, False, False, False, False, 
            True, True, True, True, True, True, True, True, True, True]

# Inizializza lo stato della sessione per le notizie mescolate
if 'notizie' not in st.session_state:
    notizie = list(zip(titoli, risposte))
    random.shuffle(notizie)
    st.session_state.notizie = notizie
else:
    notizie = st.session_state.notizie

# Inizializza lo stato della sessione per la schermata corrente
if 'screen' not in st.session_state:
    st.session_state.screen = 'info'

# CSS per incrementare il font su tutta la pagina
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 18px;
    }
    .stRadio > label {
            font-size: 18px;
    }
    .stRadio div {
            font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# Funzione per mostrare la schermata delle informazioni
def show_info():
    st.title("Benvenuto al test di predisposizione alla disinformazione")
    st.markdown("""
    ### Informazioni sul test

    Questo test è stato ideato dall'Università di Cambridge per valutare la capacità delle persone di distinguere tra notizie vere e false.   
    
    L'articolo di riferimento è disponibile [qui](https://link.springer.com/article/10.3758/s13428-023-02124-2).         
    
    In questo test ti verrà chiesto di **classificare 20 notizie come vere o false** e di rispondere ad alcune domande facoltative sul tuo background. Al termine del test potrai ricevere 3 diversi punteggi relativi alla tua capacità di:
    * **distinguere i titoli veri da quelli del falsi** (da 0% a 100%)
    * **riconoscere le notizie autentiche** (da 0% a 100%)
    * **riconoscere le notizie false** (da 0% a 100%)
    * **indice di scetticismo/creduloneria** (va da -10 a +10, da eccessivamente scettico a eccessivamente credulone)
    """)
    if st.button("Inizia il test"):
        st.session_state.screen = 'test'
        st.rerun()

# Funzione per mostrare la schermata delle domande
def show_test():
    st.title("Classifica le seguenti notizie come vere o false")

    # Raccolta delle risposte utente
    scelte_utente = []
    for i, (titolo, _) in enumerate(notizie):
        st.markdown(f"<br><div style='font-size: 18px; margin-bottom:-50px;'>{titolo}</div>", unsafe_allow_html=True)
        scelta = st.radio("", ['Reale', 'Fake'], index=None, key=f"radio_{i}")
        
        if scelta == 'Reale':
            scelte_utente.append(True)
        elif scelta == 'Fake':
            scelte_utente.append(False)
        else:
            scelte_utente.append(None)

    # Aggiungi spazio prima del bottone
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Controlla le risposte e calcola i punteggi
    if st.button("Verifica le tue risposte"):
        if None in scelte_utente:
            st.warning("Per favore, seleziona un'opzione per tutte le notizie.")
        else:
            st.session_state.scelte_utente = scelte_utente
            st.session_state.screen = 'results'
            st.rerun()

# Funzione per mostrare la schermata dei risultati
def show_results():
    scelte_utente = st.session_state.scelte_utente
    corrette = 0
    real_news_detected = 0
    fake_news_detected = 0
    total_real_news = risposte.count(True)
    total_fake_news = len(risposte) - total_real_news

    for i, (titolo, risposta_corretta) in enumerate(notizie):
        if scelte_utente[i] == risposta_corretta:
            corrette += 1
            if risposta_corretta:  # Se era una notizia vera
                real_news_detected += 1
            else:  # Se era una fake news
                fake_news_detected += 1

    # Calcolo delle metriche
    veracity_discernment = round((corrette / len(titoli)) * 100, 2)
    real_news_detection = round((real_news_detected / total_real_news) * 100, 2)
    fake_news_detection = round((fake_news_detected / total_fake_news) * 100, 2)
    distrust_naivety = real_news_detection - fake_news_detection

    # Mostra i risultati
    st.markdown(f"""
    ### Risultati del Test
    - **Veracity Discernment**: {veracity_discernment}% (abilità di distinguere accuratamente notizie vere da false)
    <br>
    - **Real News Detection**: {real_news_detection}% (abilità di identificare correttamente le notizie vere)
    <br>
    - **Fake News Detection**: {fake_news_detection}% (abilità di identificare correttamente le notizie false)
    <br>
    - **Distrust/Naïvité**: {distrust_naivety} (da -10 a +10, troppo scettico o troppo ingenuo)
    <br>
    """, unsafe_allow_html=True)

    # Commento finale in base ai risultati
    if veracity_discernment >= 80 and distrust_naivety >= -2:
        st.success("La tua capacità di riconoscere le notizie vere e false è eccellente!")
    elif veracity_discernment >= 60:
        st.info("Hai una buona capacità di distinguere le notizie, ma potresti migliorare.")
    elif veracity_discernment < 60 and distrust_naivety < 0:
        st.warning("Sembri essere un po' troppo scettico riguardo alle notizie.")
    else:
        st.error("Potresti essere più attento nella distinzione tra notizie vere e false.")

    # Aggiungi coriandoli
    rain(emoji="🎉")

# Mostra la schermata corrente
if st.session_state.screen == 'info':
    show_info()
elif st.session_state.screen == 'test':
    show_test()
elif st.session_state.screen == 'results':
    show_results()
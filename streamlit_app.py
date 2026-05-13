"""
MIST – Fake News Quiz (versione asincrona)

Quiz individuale sulla resistenza alla disinformazione.
Ogni persona risponde al proprio ritmo e vede i propri punteggi MIST.

Avvio:
  pip install streamlit pandas
  streamlit run app.py

Deploy su Streamlit Cloud:
  Connetti il repository GitHub a https://share.streamlit.io
"""

import streamlit as st
import pandas as pd

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════════

N_Q = 8

NOTIZIE = [
    ("I funzionari governativi hanno manipolato i prezzi delle azioni per nascondere scandali.", False),
    ("Nuovo studio: le persone di sinistra mentono più facilmente per ottenere uno stipendio più alto.", False),
    ("Alcuni vaccini sono carichi di sostanze chimiche e tossine pericolose.", False),
    ("Il governo sta diffondendo consapevolmente malattie attraverso le onde radio e gli alimenti.", False),
    ("Gli atteggiamenti verso l'UE sono ampiamente positivi, sia all'interno che all'esterno dell'Europa.", True),
    ("Hyatt rimuoverà le bottigliette dai bagni degli hotel entro il 2021.", True),
    ("I repubblicani sono divisi nelle opinioni sulla condotta di Trump, i democratici sono ampiamente critici.", True),
    ("Divario generazionale sul riscaldamento globale: i giovani americani sono i più preoccupati.", True),
]
assert len(NOTIZIE) == N_Q

# ═══════════════════════════════════════════════════════════════════
#  CALCOLO PUNTEGGI MIST
# ═══════════════════════════════════════════════════════════════════

def _mist(responses: list[bool]) -> dict:
    """
    Calcola punteggi MIST.
    
    responses: lista di N_Q bool (True=Reale, False=Fake) ordinata per indice domanda
    """
    n_real = sum(1 for _, correct in NOTIZIE if correct)
    n_fake = N_Q - n_real
    
    V = r = f = fj = rj = 0
    
    for i, ans in enumerate(responses):
        _, correct = NOTIZIE[i]
        if ans == correct:
            V += 1
            if correct:
                r += 1
            else:
                f += 1
        if not ans:
            fj += 1
        else:
            rj += 1
    
    d = max(0, fj - n_fake)
    n = max(0, rj - n_real)
    
    return {
        "V": V, "r": r, "f": f, "d": d, "n": n,
        "n_real": n_real, "n_fake": n_fake,
        "V_pct": round(V / N_Q * 100, 1),
        "r_pct": round(r / n_real * 100, 1) if n_real else 0.0,
        "f_pct": round(f / n_fake * 100, 1) if n_fake else 0.0,
    }


# ═══════════════════════════════════════════════════════════════════
#  PAGE SETUP + CSS
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MIST – Fake News Quiz",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 17px; }
.main .block-container { max-width: 820px; padding-top: 1.4rem; padding-bottom: 2rem; }
.big-card {
    padding: 1.3rem 1.5rem;
    border-radius: 14px;
    background: #fff;
    color: #111;
    border: 1.5px solid #e0e0e0;
    box-shadow: 0 4px 18px rgba(0,0,0,.06);
    font-size: 1.22rem;
    line-height: 1.58;
    margin-bottom: 1.1rem;
}
.badge        { font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;
                color: #888; margin-bottom: .5rem; }
div[data-testid="stHorizontalBlock"] button { height: 3.2rem; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

if "name" not in st.session_state:
    st.session_state.name = None
if "responses" not in st.session_state:
    st.session_state.responses = [None] * N_Q
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "finished" not in st.session_state:
    st.session_state.finished = False


# ═══════════════════════════════════════════════════════════════════
#  MAIN FLOW
# ═══════════════════════════════════════════════════════════════════

# ── LANDING: Inserisci nome ───────────────────────────────────────
if st.session_state.name is None:
    st.title("📰 MIST – Fake News Quiz")
    st.markdown("""
    Benvenuto al **Misinformation Susceptibility Test (MIST)**.
    
    Rispondi a 8 domande su notizie vere e false, e scopri la tua capacità 
    di distinguere la realtà dalla disinformazione.
    """)
    
    st.divider()
    st.subheader("Iniziamo")
    name = st.text_input("Il tuo nome:", max_chars=40, placeholder="Es. Mario Rossi")
    if st.button("Inizia il quiz", use_container_width=True) and name.strip():
        st.session_state.name = name.strip()
        st.rerun()

# ── QUIZ: Domande ────────────────────────────────────────────────
elif not st.session_state.finished:
    name = st.session_state.name
    cq = st.session_state.current_q
    resp = st.session_state.responses
    
    titolo, _ = NOTIZIE[cq]
    my_ans = resp[cq]
    
    st.markdown(f"<div class='badge'>Domanda {cq + 1} di {N_Q}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-card'>{titolo}</div>", unsafe_allow_html=True)
    
    st.divider()
    st.write("**Cosa ne pensi di questa notizia?**")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🟢 REALE", use_container_width=True, key="real"):
            st.session_state.responses[cq] = True
            if cq < N_Q - 1:
                st.session_state.current_q += 1
            else:
                st.session_state.finished = True
            st.rerun()
    with c2:
        if st.button("🔴 FAKE NEWS", use_container_width=True, key="fake"):
            st.session_state.responses[cq] = False
            if cq < N_Q - 1:
                st.session_state.current_q += 1
            else:
                st.session_state.finished = True
            st.rerun()
    
    if my_ans is not None:
        st.info(f"✓ Hai risposto: **{'Reale 🟢' if my_ans else 'Fake News 🔴'}**")
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("◀️ Domanda precedente", use_container_width=True, disabled=(cq == 0)):
                st.session_state.current_q = max(0, cq - 1)
                st.rerun()
        with c2:
            if cq < N_Q - 1:
                if st.button("Domanda successiva ▶️", use_container_width=True):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button("🏁 Vedi risultati", use_container_width=True):
                    st.session_state.finished = True
                    st.rerun()
        
        with st.expander("📋 Risposte finora"):
            for i in range(N_Q):
                ans = resp[i]
                if ans is None:
                    st.write(f"D.{i+1}: ⚪ Non risposto")
                else:
                    st.write(f"D.{i+1}: **{'🟢 Reale' if ans else '🔴 Fake News'}**")

# ── RESULTS: Punteggi finali ──────────────────────────────────────
elif st.session_state.finished:
    name = st.session_state.name
    resp = st.session_state.responses
    s = _mist(resp)
    
    n_real_q = s["n_real"]
    n_fake_q = s["n_fake"]
    
    st.title(f"🏁 Quiz terminato, {name}!")
    
    st.markdown("---")
    st.subheader("I tuoi risultati")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Veracity Discernment (V)",
        f"{s['V_pct']}%",
        help=f"{s['V']}/{N_Q} risposte corrette in totale.",
    )
    m2.metric(
        "Real News Detection (r)",
        f"{s['r_pct']}%",
        help=f"{s['r']}/{n_real_q} notizie reali identificate correttamente.",
    )
    m3.metric(
        "Fake News Detection (f)",
        f"{s['f_pct']}%",
        help=f"{s['f']}/{n_fake_q} fake news identificate correttamente.",
    )
    
    st.markdown("---")
    st.subheader("Bias di risposta")
    
    m4, m5 = st.columns(2)
    m4.metric(
        "Distrust (d)",
        f"{s['d']} / {n_fake_q}",
        help=(
            f"Quante volte hai detto 'Fake' in eccesso rispetto alle fake presenti. "
            f"Scala 0–{n_fake_q} (0 = nessun bias di scetticismo)."
        ),
    )
    m5.metric(
        "Naivité (n)",
        f"{s['n']} / {n_real_q}",
        help=(
            f"Quante volte hai detto 'Reale' in eccesso rispetto alle notizie vere presenti. "
            f"Scala 0–{n_real_q} (0 = nessun bias di credulità)."
        ),
    )
    
    st.caption(
        "Punteggi calcolati secondo il framework MIST *Verification done* "
        "(Maertens et al., 2024 – "
        "[articolo](https://link.springer.com/article/10.3758/s13428-023-02124-2))."
    )
    
    st.markdown("---")
    st.subheader("Tutte le tue risposte")
    
    rows = []
    for i, (titolo, correct) in enumerate(NOTIZIE):
        ans = resp[i]
        if ans is None:
            icon, note = "⚪", "non risposto"
        elif ans == correct:
            icon, note = "✅", "corretto"
        else:
            icon, note = "❌", "sbagliato"
        ans_label = "Reale" if correct else "Fake"
        rows.append({
            "N.": i + 1,
            "": icon,
            "Notizia": titolo[:60] + "…",
            "Risposta": ans_label,
            "Esito": note,
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    if st.button("🔄 Ricomincia da capo", use_container_width=True):
        st.session_state.name = None
        st.session_state.responses = [None] * N_Q
        st.session_state.current_q = 0
        st.session_state.finished = False
        st.rerun()

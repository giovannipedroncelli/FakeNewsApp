"""
MIST – Fake News Quiz (presentazione live, multi-dispositivo)

Ruoli:
  Relatore     → controlla le fasi, vede i risultati aggregati in diretta
  Partecipante → risponde dal proprio dispositivo, vede i propri punteggi alla fine

Avvio locale:
  pip install streamlit streamlit-extras pandas
  streamlit run fakenewsapp.py

Deploy su Streamlit Community Cloud:
  Rinomina requirements-fakenewsapp.txt → requirements.txt nel repository GitHub,
  poi collega il repository su https://share.streamlit.io
"""

import json
import random
import sqlite3
import time

import pandas as pd
import streamlit as st
from streamlit_extras.let_it_rain import rain

# ═══════════════════════════════════════════════════════════════════
#  CONFIG  ← cambia PRESENTER_PASSWORD prima del deploy!
# ═══════════════════════════════════════════════════════════════════
PRESENTER_PASSWORD = "relatore2026"
DB_PATH = "mist_quiz.db"
N_Q = 20        # numero domande
POLL_SECS = 2   # secondi tra un auto-refresh e l'altro (partecipanti)

# ═══════════════════════════════════════════════════════════════════
#  DATI MIST-20
# ═══════════════════════════════════════════════════════════════════
NOTIZIE: list[tuple[str, bool]] = [
    ("I funzionari governativi hanno manipolato i prezzi delle azioni per nascondere scandali.", False),
    ("I media aziendali sono controllati dal complesso militare-industriale: le principali compagnie petrolifere possiedono i media e ne controllano l'agenda.", False),
    ("Nuovo studio: le persone di sinistra mentono più facilmente per ottenere uno stipendio più alto.", False),
    ("Il governo sta manipolando la percezione pubblica dell'ingegneria genetica per rendere le persone più inclini ad accettare tali tecniche.", False),
    ("L'estremismo di sinistra causa più danni al mondo del terrorismo, afferma un rapporto dell'ONU.", False),
    ("Alcuni vaccini sono carichi di sostanze chimiche e tossine pericolose.", False),
    ("Nuovo studio: chiara relazione tra colore degli occhi e intelligenza.", False),
    ("Il governo sta diffondendo consapevolmente malattie attraverso le onde radio e gli alimenti.", False),
    ("Il virus Ebola è stato causato dai test nucleari degli Stati Uniti, afferma un nuovo studio.", False),
    ("I funzionari governativi hanno illegalmente manipolato il clima per causare tempeste devastanti.", False),
    ("Gli atteggiamenti verso l'UE sono ampiamente positivi, sia all'interno che all'esterno dell'Europa.", True),
    ("Una persona su tre nel mondo non ha fiducia nelle ONG.", True),
    ("Riflettendo il cambiamento demografico, 109 contee statunitensi sono diventate a maggioranza non-bianca dal 2000.", True),
    ("Esperti di relazioni internazionali e pubblico statunitense concordano: l'America è meno rispettata a livello globale.", True),
    ("Hyatt rimuoverà le bottigliette dai bagni degli hotel entro il 2021.", True),
    ("Il re del Marocco nomina il capo del comitato per combattere povertà e disuguaglianza.", True),
    ("I repubblicani sono divisi nelle opinioni sulla condotta di Trump, i democratici sono ampiamente critici.", True),
    ("I democratici sono più favorevoli dei repubblicani alla spesa federale per la ricerca scientifica.", True),
    ("Divario generazionale sul riscaldamento globale: i giovani americani sono i più preoccupati.", True),
    ("Il sostegno degli Stati Uniti alla marijuana legale è stabile nell'ultimo anno.", True),
]
assert len(NOTIZIE) == N_Q

# ═══════════════════════════════════════════════════════════════════
#  DATABASE  (SQLite condiviso tra tutte le sessioni Streamlit)
# ═══════════════════════════════════════════════════════════════════

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")   # letture concorrenti sicure
    return c


def _init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS game (
            id        INTEGER PRIMARY KEY DEFAULT 1,
            phase     TEXT    NOT NULL DEFAULT 'lobby',
            current_q INTEGER NOT NULL DEFAULT -1,
            q_order   TEXT    NOT NULL DEFAULT '[]'
        );
        INSERT OR IGNORE INTO game (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS participants (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL UNIQUE,
            joined_at REAL    NOT NULL DEFAULT (unixepoch())
        );

        CREATE TABLE IF NOT EXISTS responses (
            participant_id INTEGER NOT NULL,
            q_index        INTEGER NOT NULL,
            answer         INTEGER NOT NULL,
            PRIMARY KEY (participant_id, q_index)
        );
        """)


_init_db()


def _game() -> dict:
    with _conn() as c:
        row = c.execute("SELECT phase, current_q, q_order FROM game WHERE id=1").fetchone()
    return {"phase": row["phase"], "cq": row["current_q"], "order": json.loads(row["q_order"])}


def _game_set(**kw):
    sets, vals = [], []
    for k, v in kw.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v) if k == "q_order" else v)
    with _conn() as c:
        c.execute(f"UPDATE game SET {','.join(sets)} WHERE id=1", vals)


def _join(name: str) -> int:
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO participants (name) VALUES (?)", (name,))
        return c.execute("SELECT id FROM participants WHERE name=?", (name,)).fetchone()["id"]


def _participants() -> list:
    with _conn() as c:
        return c.execute("SELECT id, name FROM participants ORDER BY joined_at").fetchall()


def _save(pid: int, qi: int, ans: bool):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO responses (participant_id, q_index, answer) VALUES (?,?,?)",
            (pid, qi, int(ans)),
        )


def _get(pid: int, qi: int):
    with _conn() as c:
        row = c.execute(
            "SELECT answer FROM responses WHERE participant_id=? AND q_index=?", (pid, qi)
        ).fetchone()
    return None if row is None else bool(row["answer"])


def _resps_q(qi: int) -> dict:
    """pid → answer_bool per la domanda qi"""
    with _conn() as c:
        rows = c.execute(
            "SELECT participant_id, answer FROM responses WHERE q_index=?", (qi,)
        ).fetchall()
    return {r["participant_id"]: bool(r["answer"]) for r in rows}


def _resps_p(pid: int) -> dict:
    """qi → answer_bool per il partecipante pid"""
    with _conn() as c:
        rows = c.execute(
            "SELECT q_index, answer FROM responses WHERE participant_id=?", (pid,)
        ).fetchall()
    return {r["q_index"]: bool(r["answer"]) for r in rows}


def _reset():
    with _conn() as c:
        c.executescript("""
        DELETE FROM responses;
        DELETE FROM participants;
        UPDATE game SET phase='lobby', current_q=-1, q_order='[]' WHERE id=1;
        """)


# ═══════════════════════════════════════════════════════════════════
#  CALCOLO PUNTEGGI MIST  (Verification done: V, r, f, d, n)
#  Fonte: MIST Implementation Guide, OSF https://osf.io/r7phc/
#    V = somma risposte corrette su tutti gli item
#    r = corrette sugli item reali
#    f = corrette sugli item fake
#    d = max(0, #giudizi_fake - #item_fake)      [0..10]
#    n = max(0, #giudizi_reale - #item_reali)    [0..10]
# ═══════════════════════════════════════════════════════════════════

def _mist(resp: dict, order: list) -> dict:
    n_real = sum(1 for qi in order if NOTIZIE[qi][1])
    n_fake = len(order) - n_real
    V = r = f = fj = rj = 0

    for qi in order:
        ans = resp.get(qi)
        if ans is None:
            continue
        _, correct = NOTIZIE[qi]
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
    initial_sidebar_state="expanded",
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
.correct-card { border-color: #2e7d32 !important; background: #e8f5e9 !important; color: #1b5e20 !important; }
.wrong-card   { border-color: #c62828 !important; background: #ffebee !important; color: #8e0000 !important; }
.badge        { font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;
                color: #888; margin-bottom: .5rem; }
div[data-testid="stHorizontalBlock"] button { height: 3.2rem; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR – scelta del ruolo
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📰 MIST Quiz")
    if "role" not in st.session_state:
        st.markdown("Seleziona il tuo ruolo:")
        if st.button("👤 Sono un partecipante", use_container_width=True):
            st.session_state.role = "participant"
            st.rerun()
        if st.button("🎙️ Sono il relatore", use_container_width=True):
            st.session_state.role = "presenter"
            st.rerun()
    else:
        label = "🎙️ Relatore" if st.session_state.role == "presenter" else "👤 Partecipante"
        st.write(f"Ruolo: **{label}**")
        if st.button("↩️ Cambia ruolo", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  VISTA RELATORE
# ═══════════════════════════════════════════════════════════════════

def _presenter():
    # ── autenticazione ─────────────────────────────────────────
    if not st.session_state.get("auth"):
        st.title("🎙️ Accesso relatore")
        pwd = st.text_input("Password", type="password")
        if st.button("Accedi", use_container_width=True):
            if pwd == PRESENTER_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Password errata.")
        return

    gs    = _game()
    phase = gs["phase"]
    order = gs["order"]
    cq    = gs["cq"]
    pts   = _participants()
    n_pts = len(pts)

    st.markdown(
        f"<div class='badge'>Fase: {phase.upper()} · {n_pts} partecipanti connessi</div>",
        unsafe_allow_html=True,
    )

    # ── LOBBY ──────────────────────────────────────────────────
    if phase == "lobby":
        st.title("🎙️ Sala d'attesa")
        if pts:
            st.write("**Partecipanti connessi:**")
            for p in pts:
                st.write(f"- {p['name']}")
        else:
            st.info("Nessun partecipante ancora connesso.")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ Avvia il quiz", use_container_width=True, disabled=(n_pts == 0)):
                new_order = list(range(N_Q))
                random.shuffle(new_order)
                _game_set(phase="question", current_q=0, q_order=new_order)
                st.rerun()
        with c2:
            if st.button("🔄 Aggiorna lista", use_container_width=True):
                st.rerun()

        with st.expander("⚙️ Reimposta (elimina tutti i dati)"):
            if st.button("🗑️ Reimposta quiz", type="secondary", use_container_width=True):
                _reset()
                st.rerun()

    # ── QUESTION ───────────────────────────────────────────────
    elif phase == "question":
        qi     = order[cq]
        titolo = NOTIZIE[qi][0]

        st.title(f"Domanda {cq + 1} / {N_Q}")
        st.markdown(f"<div class='big-card'>{titolo}</div>", unsafe_allow_html=True)

        resps   = _resps_q(qi)
        n_ans   = len(resps)
        n_reale = sum(1 for v in resps.values() if v)
        n_fake  = n_ans - n_reale

        st.progress(n_ans / max(n_pts, 1), text=f"Risposte ricevute: {n_ans} / {n_pts}")
        m1, m2 = st.columns(2)
        m1.metric("🟢 Reale", n_reale)
        m2.metric("🔴 Fake", n_fake)

        st.divider()
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔍 Svela la risposta", use_container_width=True):
                _game_set(phase="reveal")
                st.rerun()
        with b2:
            if st.button("🔄 Aggiorna", use_container_width=True):
                st.rerun()

    # ── REVEAL ─────────────────────────────────────────────────
    elif phase == "reveal":
        qi = order[cq]
        titolo, correct = NOTIZIE[qi]

        st.title(f"Risposta – Domanda {cq + 1} / {N_Q}")
        correct_label = "✅ REALE" if correct else "❌ FAKE NEWS"
        css_cls = "correct-card" if correct else "wrong-card"
        st.markdown(
            f"<div class='big-card {css_cls}'>{titolo}"
            f"<br><br><strong style='font-size:1.05em'>{correct_label}</strong></div>",
            unsafe_allow_html=True,
        )

        resps     = _resps_q(qi)
        n_ans     = len(resps)
        n_correct = sum(1 for ans in resps.values() if ans == correct)
        n_reale   = sum(1 for v in resps.values() if v)
        n_fake    = n_ans - n_reale

        c1, c2, c3 = st.columns(3)
        c1.metric("Risposte", f"{n_ans}/{n_pts}")
        c2.metric("✅ Corrette", f"{n_correct} ({round(n_correct / max(n_ans, 1) * 100)}%)")
        c3.metric("❌ Errate", n_ans - n_correct)

        df_chart = pd.DataFrame(
            {"Risposta": ["Reale", "Fake"], "Voti": [n_reale, n_fake]}
        )
        st.bar_chart(df_chart.set_index("Risposta"))

        st.divider()
        if cq < N_Q - 1:
            if st.button("▶️ Prossima domanda", use_container_width=True):
                _game_set(phase="question", current_q=cq + 1)
                st.rerun()
        else:
            if st.button("🏁 Mostra risultati finali", use_container_width=True):
                _game_set(phase="finished")
                st.rerun()

    # ── FINISHED ───────────────────────────────────────────────
    elif phase == "finished":
        st.title("🏁 Risultati finali del gruppo")
        rain(emoji="🎉")

        all_scores = []
        for p in _participants():
            resp = _resps_p(p["id"])
            s = _mist(resp, order)
            all_scores.append({"Nome": p["name"], **s})

        if all_scores:
            def _avg(key):
                return round(sum(sc[key] for sc in all_scores) / len(all_scores), 1)

            st.subheader("📊 Media del gruppo")
            m1, m2, m3 = st.columns(3)
            m1.metric("Veracity Discernment (V)", f"{_avg('V_pct')}%")
            m2.metric("Real News Detection (r)", f"{_avg('r_pct')}%")
            m3.metric("Fake News Detection (f)", f"{_avg('f_pct')}%")
            m4, m5, _ = st.columns(3)
            m4.metric("Distrust (d)", _avg("d"),
                      help="Media: tendenza a giudicare in eccesso come fake (0–10)")
            m5.metric("Naivite (n)", _avg("n"),
                      help="Media: tendenza a giudicare in eccesso come reale (0–10)")

            st.divider()
            st.subheader("🏆 Classifica partecipanti")
            df = pd.DataFrame(all_scores)[["Nome", "V_pct", "r_pct", "f_pct", "d", "n"]]
            df.columns = ["Nome", "V %", "r %", "f %", "d", "n"]
            df = df.sort_values("V %", ascending=False).reset_index(drop=True)
            df.index += 1
            st.dataframe(df, use_container_width=True)

            with st.expander("📋 Distribuzione risposte per domanda"):
                rows = []
                for pos, qi in enumerate(order):
                    titolo, correct = NOTIZIE[qi]
                    resps = _resps_q(qi)
                    n_ans = len(resps)
                    n_ok = sum(1 for a in resps.values() if a == correct)
                    rows.append({
                        "#": pos + 1,
                        "Notizia": titolo[:72] + "…",
                        "Corretta": "Reale" if correct else "Fake",
                        "Risposte": n_ans,
                        "Corrette %": f"{round(n_ok / max(n_ans, 1) * 100)}%",
                    })
                st.dataframe(
                    pd.DataFrame(rows).set_index("#"),
                    use_container_width=True,
                )

        st.divider()
        if st.button("🔄 Nuovo quiz", use_container_width=True):
            _reset()
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  VISTA PARTECIPANTE
# ═══════════════════════════════════════════════════════════════════

def _participant():
    gs    = _game()
    phase = gs["phase"]
    order = gs["order"]
    cq    = gs["cq"]

    # ── iscrizione ─────────────────────────────────────────────
    if "pid" not in st.session_state:
        st.title("📰 MIST Quiz")
        st.markdown("Inserisci il tuo nome per partecipare.")
        name = st.text_input("Nome", max_chars=40, placeholder="Es. Mario Rossi")
        if st.button("Partecipa", use_container_width=True) and name.strip():
            if phase == "finished":
                st.warning("Il quiz è già terminato. Riprova alla prossima sessione.")
            else:
                pid = _join(name.strip())
                st.session_state.pid   = pid
                st.session_state.pname = name.strip()
                st.rerun()
        return

    pid   = st.session_state.pid
    pname = st.session_state.pname

    # ── LOBBY ──────────────────────────────────────────────────
    if phase == "lobby":
        st.title(f"Ciao, {pname}! 👋")
        st.success("✅ Connesso! In attesa che il relatore avvii il quiz...")
        st.caption(f"La pagina si aggiorna ogni {POLL_SECS} secondi.")
        time.sleep(POLL_SECS)
        st.rerun()

    # ── QUESTION ───────────────────────────────────────────────
    elif phase == "question":
        qi     = order[cq]
        titolo = NOTIZIE[qi][0]
        my_ans = _get(pid, qi)

        st.markdown(
            f"<div class='badge'>Domanda {cq + 1} di {N_Q}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='big-card'>{titolo}</div>", unsafe_allow_html=True)

        if my_ans is None:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🟢 REALE", use_container_width=True):
                    _save(pid, qi, True)
                    st.rerun()
            with b2:
                if st.button("🔴 FAKE NEWS", use_container_width=True):
                    _save(pid, qi, False)
                    st.rerun()
            # auto-refresh: rileva se il relatore passa alla reveal
            st.caption(f"La pagina si aggiorna ogni {POLL_SECS} secondi.")
            time.sleep(POLL_SECS)
            st.rerun()
        else:
            label = "REALE 🟢" if my_ans else "FAKE NEWS 🔴"
            st.info(f"Hai risposto: **{label}**")
            st.caption("In attesa che il relatore sveli la risposta...")
            time.sleep(POLL_SECS)
            st.rerun()

    # ── REVEAL ─────────────────────────────────────────────────
    elif phase == "reveal":
        qi = order[cq]
        titolo, correct = NOTIZIE[qi]
        my_ans = _get(pid, qi)

        st.markdown(
            f"<div class='badge'>Domanda {cq + 1} di {N_Q} – Risposta</div>",
            unsafe_allow_html=True,
        )
        correct_label = "✅ REALE" if correct else "❌ FAKE NEWS"
        css_cls = "correct-card" if correct else "wrong-card"
        st.markdown(
            f"<div class='big-card {css_cls}'>{titolo}"
            f"<br><br><strong>Risposta corretta: {correct_label}</strong></div>",
            unsafe_allow_html=True,
        )

        if my_ans is None:
            st.warning("Non hai risposto a questa domanda.")
        elif my_ans == correct:
            st.success("🎯 Corretto!")
        else:
            my_label = "REALE" if my_ans else "FAKE NEWS"
            st.error(f"❌ Sbagliato – hai risposto {my_label}.")

        st.caption("In attesa della prossima domanda...")
        time.sleep(POLL_SECS)
        st.rerun()

    # ── FINISHED ───────────────────────────────────────────────
    elif phase == "finished":
        st.title(f"🏁 Quiz terminato, {pname}!")
        rain(emoji="🎉")

        resp = _resps_p(pid)
        s    = _mist(resp, order)

        st.subheader("I tuoi risultati")
        m1, m2, m3 = st.columns(3)
        m1.metric("Veracity Discernment (V)", f"{s['V_pct']}%",
                  help=f"{s['V']}/{N_Q} risposte corrette")
        m2.metric("Real News Detection (r)", f"{s['r_pct']}%",
                  help=f"{s['r']}/10 notizie reali identificate")
        m3.metric("Fake News Detection (f)", f"{s['f_pct']}%",
                  help=f"{s['f']}/10 fake news identificate")
        m4, m5, _ = st.columns(3)
        m4.metric("Distrust (d)", s["d"],
                  help="Quante volte hai detto 'Fake' in eccesso (0 = nessun bias, 10 = massimo)")
        m5.metric("Naivite (n)", s["n"],
                  help="Quante volte hai detto 'Reale' in eccesso (0 = nessun bias, 10 = massimo)")

        st.caption(
            "Punteggi calcolati secondo il framework MIST *Verification done* "
            "(Maertens et al., 2024 – "
            "[articolo](https://link.springer.com/article/10.3758/s13428-023-02124-2))."
        )

        if s["V_pct"] >= 80 and s["d"] <= 2 and s["n"] <= 2:
            st.success("Eccellente capacità di riconoscimento delle notizie!")
        elif s["V_pct"] >= 60:
            st.info("Buona capacità, ma con margini di miglioramento.")
        elif s["d"] > s["n"]:
            st.warning("Tendi ad essere un po' troppo scettico/a.")
        else:
            st.error("Fai fatica a distinguere notizie vere da false.")

        with st.expander("📋 Rivedi tutte le tue risposte"):
            for pos, qi in enumerate(order):
                titolo, correct = NOTIZIE[qi]
                my_ans = resp.get(qi)
                if my_ans is None:
                    icon, note = "⚪", "non risposto"
                elif my_ans == correct:
                    icon, note = "✅", "corretto"
                else:
                    icon, note = "❌", "sbagliato"
                ans_label = "Reale" if correct else "Fake"
                st.markdown(
                    f"{icon} **D.{pos + 1}** {titolo}  \n"
                    f"→ Risposta: *{ans_label}* · {note}"
                )


# ═══════════════════════════════════════════════════════════════════
#  ROUTING
# ═══════════════════════════════════════════════════════════════════

role = st.session_state.get("role")

if role is None:
    st.title("📰 MIST – Fake News Quiz")
    st.markdown("""
    Benvenuto al **Misinformation Susceptibility Test (MIST)**.

    Usa il pannello laterale per selezionare il tuo ruolo:

    - **👤 Partecipante** – rispondi al quiz dal tuo dispositivo
    - **🎙️ Relatore** – controlla il flusso e mostra i risultati sul grande schermo
    """)
elif role == "presenter":
    _presenter()
else:
    _participant()


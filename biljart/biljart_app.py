import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="🎱 K.B.C. De Biekens",
    page_icon="🎱",
    layout="wide"
)

BESTAND = "spelers.csv"

# ======================
# DATA INIT
# ======================
if not os.path.exists(BESTAND):
    df_init = pd.DataFrame(columns=[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten"
    ])
    df_init.to_csv(BESTAND, index=False)

df = pd.read_csv(BESTAND)

# ======================
# CSS (PRO SPORT UI)
# ======================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top, #0b2a1d, #06150f 70%);
}

/* TITLES */
h1 {
    color: #d4af37 !important;
    font-weight: 900;
    letter-spacing: 1px;
}

h2, h3 {
    color: #f5d77b !important;
}

/* CARD */
.card {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(212,175,55,0.35);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.4);
    transition: all 0.25s ease;
}

.card:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: #d4af37;
}

/* AVATAR */
.avatar {
    width: 55px;
    height: 55px;
    border-radius: 50%;
    background: linear-gradient(135deg, #d4af37, #f5d77b);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: black;
    font-size: 18px;
    margin-bottom: 10px;
}

/* BUTTONS */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #d4af37, #f5d77b);
    color: black;
    font-weight: 800;
    border-radius: 12px;
    height: 45px;
    border: none;
}

.stButton > button:hover {
    transform: scale(1.02);
    opacity: 0.95;
}

/* METRICS */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(212,175,55,0.25);
    border-radius: 14px;
    padding: 12px;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #071a12;
}

</style>
""", unsafe_allow_html=True)

# ======================
# HANDICAP LOGICA
# ======================
def bereken_handicap(row):
    if row["Totaal Beurten"] > 0:
        moyenne = row["Totaal Punten"] / row["Totaal Beurten"]
    else:
        moyenne = 0
    return round(moyenne * 25), moyenne

# ======================
# SIDEBAR
# ======================
menu = st.sidebar.radio("📊 Navigatie", ["🏠 Home", "👤 Spelers", "🏆 Ranking"])

# =========================================================
# HOME
# =========================================================
if menu == "🏠 Home":
    st.title("🎱 K.B.C. De Biekens Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class="card">
        <h3>👥 Spelers</h3>
        <h1>{len(df)}</h1>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="card">
        <h3>🎮 Wedstrijden</h3>
        <h1>{int(df["Wedstrijden"].sum())}</h1>
    </div>
    """, unsafe_allow_html=True)

    club_moy = df["Totaal Punten"].sum() / max(1, df["Totaal Beurten"].sum())

    col3.markdown(f"""
    <div class="card">
        <h3>📊 Club moyenne</h3>
        <h1>{club_moy:.3f}</h1>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# SPELERS
# =========================================================
elif menu == "👤 Spelers":
    st.title("👤 Spelersbeheer")

    st.subheader("➕ Nieuwe speler")
    naam = st.text_input("Naam speler")

    if st.button("Toevoegen"):
        if naam.strip():
            if naam.lower() in df["Speler"].str.lower().values:
                st.warning("Speler bestaat al.")
            else:
                df = pd.concat([df, pd.DataFrame([{
                    "Speler": naam,
                    "Wedstrijden": 0,
                    "Totaal Punten": 0,
                    "Totaal Beurten": 0
                }])], ignore_index=True)

                df.to_csv(BESTAND, index=False)
                st.success("Toegevoegd!")
                st.rerun()

    st.divider()

    st.subheader("🗑 Verwijderen")

    if len(df) > 0:
        speler_del = st.selectbox("Selecteer speler", df["Speler"])

        if st.button("Verwijder"):
            df = df[df["Speler"] != speler_del]
            df.to_csv(BESTAND, index=False)
            st.success("Verwijderd")
            st.rerun()

    st.divider()

    st.subheader("🎮 Wedstrijd invoeren")

    if len(df) > 0:
        speler = st.selectbox("Speler", df["Speler"])

        idx = df[df["Speler"] == speler].index[0]

        col1, col2 = st.columns(2)

        punten = col1.number_input("Punten", min_value=0)
        beurten = col2.number_input("Beurten", min_value=1, value=25)

        if st.button("Opslaan"):
            if df.loc[idx, "Wedstrijden"] < 22:
                df.loc[idx, "Wedstrijden"] += 1
                df.loc[idx, "Totaal Punten"] += punten
                df.loc[idx, "Totaal Beurten"] += beurten

                df.to_csv(BESTAND, index=False)
                st.success("Opgeslagen")
                st.rerun()
            else:
                st.error("Max 22 wedstrijden bereikt")

    st.divider()

    st.subheader("📊 Speler detail")

    if len(df) > 0:
        row = df.loc[idx]
        handicap, moyenne = bereken_handicap(row)

        st.metric("Wedstrijden", f"{row['Wedstrijden']}/22")
        st.metric("Moyenne", f"{moyenne:.3f}")
        st.metric("Handicap", handicap)

        st.dataframe(pd.DataFrame([row]), width="stretch")

# =========================================================
# RANKING
# =========================================================
elif menu == "🏆 Ranking":
    st.title("🏆 Ranking")

    if len(df) == 0:
        st.info("Geen spelers")
        st.stop()

    ranking = df.copy()

    ranking["Moyenne"] = ranking.apply(
        lambda r: (r["Totaal Punten"] / r["Totaal Beurten"])
        if r["Totaal Beurten"] > 0 else 0,
        axis=1
    )

    ranking["Handicap"] = (ranking["Moyenne"] * 25).round().astype(int)

    ranking = ranking.sort_values("Handicap", ascending=False)

    # ======================
    # PODIUM (PRO UI)
    # ======================
    st.subheader("🏆 Podium")

    medals = ["🥇", "🥈", "🥉"]

    cols = st.columns(3)

    for i in range(min(3, len(ranking))):
        speler = ranking.iloc[i]["Speler"]
        handicap = ranking.iloc[i]["Handicap"]

        initials = "".join([x[0] for x in speler.split()]).upper()

        cols[i].markdown(f"""
        <div class="card">
            <div class="avatar">{initials}</div>
            <h2>{medals[i]} {speler}</h2>
            <h3>Handicap: {handicap}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 Volledige ranking")

    st.dataframe(ranking, width="stretch", hide_index=True)
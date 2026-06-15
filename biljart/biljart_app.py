import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="🎱 K.B.C. De Biekens Pro Dashboard",
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
# CSS (PRO UI)
# ======================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #06150f 0%, #0b2a1d 50%, #06150f 100%);
}

h1, h2, h3 {
    color: #d4af37 !important;
}

p, label, div {
    color: white;
}

/* Cards */
.card {
    background: rgba(15, 40, 25, 0.75);
    border: 1px solid #d4af37;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 0 20px rgba(0,0,0,0.3);
}

/* Buttons */
.stButton > button {
    width: 100%;
    background-color: #d4af37;
    color: black;
    font-weight: bold;
    border-radius: 10px;
    height: 45px;
}

.stButton > button:hover {
    background-color: #e8c766;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #d4af37;
    border-radius: 12px;
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
# SIDEBAR NAV
# ======================
menu = st.sidebar.radio("📊 Navigatie", ["🏠 Home", "👤 Spelers", "🏆 Ranking"])

# =========================================================
# HOME
# =========================================================
if menu == "🏠 Home":
    st.title("🎱 K.B.C. De Biekens Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.markdown('<div class="card">', unsafe_allow_html=True)
    col1.metric("Aantal spelers", len(df))
    col1.markdown('</div>', unsafe_allow_html=True)

    totaal_wedstrijden = df["Wedstrijden"].sum()
    col2.markdown('<div class="card">', unsafe_allow_html=True)
    col2.metric("Totaal wedstrijden", int(totaal_wedstrijden))
    col2.markdown('</div>', unsafe_allow_html=True)

    gemiddelde_speler = len(df) and (df["Totaal Punten"].sum() / max(1, df["Totaal Beurten"].sum())) or 0
    col3.markdown('<div class="card">', unsafe_allow_html=True)
    col3.metric("Club moyenne", f"{gemiddelde_speler:.3f}")
    col3.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# SPELERS
# =========================================================
elif menu == "👤 Spelers":
    st.title("👤 Spelersbeheer")

    st.markdown("### ➕ Nieuwe speler")

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

    st.markdown("### 🗑️ Verwijderen")

    if len(df) > 0:
        del_speler = st.selectbox("Selecteer speler", df["Speler"])

        if st.button("Verwijder"):
            df = df[df["Speler"] != del_speler]
            df.to_csv(BESTAND, index=False)
            st.success("Verwijderd")
            st.rerun()

    st.divider()

    st.markdown("### 🎮 Wedstrijd invoeren")

    if len(df) > 0:
        speler = st.selectbox("Speler", df["Speler"])

        idx = df[df["Speler"] == speler].index[0]

        col1, col2 = st.columns(2)

        punten = col1.number_input("Punten", min_value=0, value=0)
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

        st.markdown("### 📊 Speler profiel")

        row = df.loc[idx]
        handicap, moyenne = bereken_handicap(row)

        c1, c2, c3, c4 = st.columns(4)

        c1.markdown('<div class="card">', unsafe_allow_html=True)
        c1.metric("Wedstrijden", f"{row['Wedstrijden']}/22")
        c1.markdown('</div>', unsafe_allow_html=True)

        c2.markdown('<div class="card">', unsafe_allow_html=True)
        c2.metric("Moyenne", f"{moyenne:.3f}")
        c2.markdown('</div>', unsafe_allow_html=True)

        c3.markdown('<div class="card">', unsafe_allow_html=True)
        c3.metric("Handicap", handicap)
        c3.markdown('</div>', unsafe_allow_html=True)

        c4.markdown('<div class="card">', unsafe_allow_html=True)
        c4.metric("Resterend", max(0, 22 - row["Wedstrijden"]))
        c4.markdown('</div>', unsafe_allow_html=True)

        st.markdown("### 📋 Data")
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

# =========================================================
# RANKING
# =========================================================
elif menu == "🏆 Ranking":
    st.title("🏆 Ranking")

    if len(df) > 0:
        ranking = df.copy()

        ranking["Moyenne"] = ranking.apply(
            lambda r: (r["Totaal Punten"] / r["Totaal Beurten"]) if r["Totaal Beurten"] > 0 else 0,
            axis=1
        )

        ranking["Handicap"] = (ranking["Moyenne"] * 25).round().astype(int)

        ranking = ranking.sort_values("Handicap", ascending=False)

        st.markdown("### 🥇 Podium")

        top3 = ranking.head(3).reset_index(drop=True)

        cols = st.columns(3)

        for i in range(min(3, len(top3))):
            cols[i].markdown(f"""
            <div class="card">
                <h2>#{i+1} {top3.loc[i, 'Speler']}</h2>
                <p>Handicap: <b>{top3.loc[i, 'Handicap']}</b></p>
                <p>Moyenne: {top3.loc[i, 'Moyenne']:.3f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### 📊 Volledige ranking")
        st.dataframe(ranking, use_container_width=True)

    else:
        st.info("Nog geen spelers")
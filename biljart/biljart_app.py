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
# CSS
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

.card {
    background: rgba(15, 40, 25, 0.75);
    border: 1px solid #d4af37;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 0 20px rgba(0,0,0,0.3);
}

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

    col2.markdown('<div class="card">', unsafe_allow_html=True)
    col2.metric("Wedstrijden", int(df["Wedstrijden"].sum()))
    col2.markdown('</div>', unsafe_allow_html=True)

    club_moy = (
        df["Totaal Punten"].sum() / max(1, df["Totaal Beurten"].sum())
    )

    col3.markdown('<div class="card">', unsafe_allow_html=True)
    col3.metric("Club moyenne", f"{club_moy:.3f}")
    col3.markdown('</div>', unsafe_allow_html=True)

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

        st.dataframe(
            pd.DataFrame([row]),
            width="stretch"
        )

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

    st.subheader("🥇 Top 3")

    cols = st.columns(3)

    for i in range(min(3, len(ranking))):
        cols[i].metric(
            ranking.iloc[i]["Speler"],
            ranking.iloc[i]["Handicap"]
        )

    st.divider()

    st.subheader("📊 Volledige ranking")

    st.dataframe(ranking, width="stretch")
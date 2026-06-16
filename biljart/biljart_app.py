import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="🎱 K.B.C. De Biekens",
    page_icon="🎱",
    layout="wide"
)

# ======================
# FILES
# ======================
PLAYERS_FILE = "spelers.csv"
MATCHES_FILE = "wedstrijden.csv"

# ======================
# INIT FILES
# ======================
if not os.path.exists(PLAYERS_FILE):
    pd.DataFrame(columns=[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten"
    ]).to_csv(PLAYERS_FILE, index=False)

if not os.path.exists(MATCHES_FILE):
    pd.DataFrame(columns=[
        "Speler",
        "Tegenstander",
        "Punten",
        "Beurten",
        "Winnaar"
    ]).to_csv(MATCHES_FILE, index=False)

df = pd.read_csv(PLAYERS_FILE)
matches = pd.read_csv(MATCHES_FILE)

# ======================
# STYLE
# ======================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #0b2a1d, #06150f 70%);
}

h1 {
    color: #d4af37 !important;
    font-weight: 900;
}

.card {
    background: rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(212,175,55,0.3);
}
</style>
""", unsafe_allow_html=True)

# ======================
# HANDICAP
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
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🏆 Ranking",
    "📊 Stats"
])

# =========================================================
# HOME
# =========================================================
if menu == "🏠 Home":
    st.title("🎱 K.B.C. De Biekens")

    col1, col2, col3 = st.columns(3)

    col1.metric("Spelers", len(df))
    col2.metric("Wedstrijden", len(matches))
    col3.metric("Totaal punten", int(df["Totaal Punten"].sum()))

# =========================================================
# SPELERS
# =========================================================
elif menu == "👤 Spelers":
    st.title("👤 Spelersbeheer")

    naam = st.text_input("Nieuwe speler")

    if st.button("Toevoegen"):
        if naam.strip():
            if naam.lower() not in df["Speler"].str.lower().values:
                df = pd.concat([df, pd.DataFrame([{
                    "Speler": naam,
                    "Wedstrijden": 0,
                    "Totaal Punten": 0,
                    "Totaal Beurten": 0
                }])], ignore_index=True)

                df.to_csv(PLAYERS_FILE, index=False)
                st.success("Toegevoegd")
                st.rerun()

    st.divider()

    st.subheader("🎮 Wedstrijd invoeren")

    if len(df) > 0:
        speler = st.selectbox("Speler", df["Speler"])
        idx = df[df["Speler"] == speler].index[0]

        punten = st.number_input("Punten", min_value=0)
        beurten = st.number_input("Beurten", min_value=1, value=25)

        if st.button("Opslaan wedstrijd"):

            # 👉 OFFICIËLE HANDICAP UPDATE (blijft jouw systeem)
            df.loc[idx, "Wedstrijden"] += 1
            df.loc[idx, "Totaal Punten"] += punten
            df.loc[idx, "Totaal Beurten"] += beurten

            df.to_csv(PLAYERS_FILE, index=False)

            # 👉 EXTRA LOG (voor stats)
            new_match = pd.DataFrame([{
                "Speler": speler,
                "Tegenstander": "",
                "Punten": punten,
                "Beurten": beurten,
                "Winnaar": speler if punten > 0 else ""
            }])

            matches = pd.concat([matches, new_match], ignore_index=True)
            matches.to_csv(MATCHES_FILE, index=False)

            st.success("Opgeslagen")
            st.rerun()

# =========================================================
# RANKING
# =========================================================
elif menu == "🏆 Ranking":
    st.title("🏆 Ranking")

    ranking = df.copy()

    ranking["Moyenne"] = ranking.apply(
        lambda r: r["Totaal Punten"] / r["Totaal Beurten"]
        if r["Totaal Beurten"] > 0 else 0,
        axis=1
    )

    ranking["Handicap"] = (ranking["Moyenne"] * 25).round().astype(int)

    ranking = ranking.sort_values("Handicap", ascending=False)

    st.subheader("🏆 Podium")

    medals = ["🥇", "🥈", "🥉"]

    cols = st.columns(3)

    for i in range(min(3, len(ranking))):
        cols[i].markdown(f"""
        <div class="card">
            <h2>{medals[i]} {ranking.iloc[i]['Speler']}</h2>
            <h3>Handicap: {ranking.iloc[i]['Handicap']}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.dataframe(ranking, width="stretch", hide_index=True)

# =========================================================
# STATS
# =========================================================
elif menu == "📊 Stats":
    st.title("📊 Statistieken")

    if len(matches) == 0:
        st.info("Geen data")
        st.stop()

    st.subheader("🏆 Meeste gewonnen matches")
    st.dataframe(matches["Winnaar"].value_counts())

    st.subheader("⚡ Kortste partij")
    st.write(matches.loc[matches["Beurten"].idxmin()])
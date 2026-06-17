import streamlit as st
import pandas as pd
import os
from datetime import date

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
        "Totaal Punten",
        "Totaal Beurten",
        "Wedstrijden"
    ]).to_csv(PLAYERS_FILE, index=False)

if not os.path.exists(MATCHES_FILE):
    pd.DataFrame(columns=[
        "Datum", "Periode",
        "Speler1", "Speler2",
        "Handicap1", "Handicap2",
        "Caramboles1", "Caramboles2",
        "Beurten",
        "Winnaar",
        "Punten1", "Punten2"
    ]).to_csv(MATCHES_FILE, index=False)

df = pd.read_csv(PLAYERS_FILE)
matches = pd.read_csv(MATCHES_FILE)

# ======================
# SAFE NUMBERS
# ======================
for col in ["Totaal Punten", "Totaal Beurten", "Wedstrijden"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col in ["Beurten", "Punten1", "Punten2"]:
    matches[col] = pd.to_numeric(matches[col], errors="coerce").fillna(0)

# ======================
# STYLE
# ======================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #0b3d2e, #061a14 75%);
    color: white;
}
h1 { color: #d4af37; }
h2, h3 { color: #f5d77b; }
</style>
""", unsafe_allow_html=True)

# ======================
# FUNCTIONS
# ======================

def punten_win(beurten):
    return round(max(0.2, 10 - (beurten - 1) * 0.2), 2)

def periode(d):
    m = pd.to_datetime(d).month
    return "H1" if m <= 6 else "H2"

# 🎯 NIEUWE FUNCTIE (JOUW FORMULE)
def speelpunten(gemaakt, beurten):
    if beurten == 0:
        return 0
    return round((gemaakt / beurten) * 25, 3)

# ======================
# MENU
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🎮 Match",
    "🏆 Ranking",
    "📊 Stats",
    "🧮 Speelpunten calculator",
    "👑 Kampioenschap"
])

# ======================
# HOME
# ======================
if menu == "🏠 Home":

    st.title("🎱 K.B.C. De Biekens")

    col1, col2, col3 = st.columns(3)
    col1.metric("Spelers", len(df))
    col2.metric("Wedstrijden", len(matches))
    col3.metric("Totaal punten", round(df["Totaal Punten"].sum(), 2))

# ======================
# SPELERS
# ======================
elif menu == "👤 Spelers":

    st.title("👤 Spelers")

    naam = st.text_input("Nieuwe speler")

    if st.button("Toevoegen"):
        if naam.strip():
            df.loc[len(df)] = [naam, 0, 0, 0]
            df.to_csv(PLAYERS_FILE, index=False)
            st.rerun()

    st.divider()

    if len(df) > 0:
        delsp = st.selectbox("Verwijder speler", df["Speler"])

        if st.button("Verwijderen"):
            df = df[df["Speler"] != delsp]
            matches = matches[
                (matches["Speler1"] != delsp) &
                (matches["Speler2"] != delsp)
            ]

            df.to_csv(PLAYERS_FILE, index=False)
            matches.to_csv(MATCHES_FILE, index=False)
            st.rerun()

# ======================
# MATCH
# ======================
elif menu == "🎮 Match":

    st.title("🎮 Match invoeren")

    if len(df) > 0:

        s1 = st.selectbox("Speler 1", df["Speler"])
        s2 = st.selectbox("Speler 2", df[df["Speler"] != s1]["Speler"])

        d = st.date_input("Datum", value=date.today())
        per = periode(d)

        h1 = st.number_input("Handicap 1", 1)
        h2 = st.number_input("Handicap 2", 1)

        c1 = st.number_input("Caramboles 1", 0)
        c2 = st.number_input("Caramboles 2", 0)

        beurten = st.number_input("Beurten winnaar", 1)
        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan"):

            idx1 = df.index[df["Speler"] == s1][0]
            idx2 = df.index[df["Speler"] == s2][0]

            p1 = 0
            p2 = 0

            if winnaar == s1:
                p1 = punten_win(beurten)
                df.at[idx1, "Wedstrijden"] += 1
            else:
                p2 = punten_win(beurten)
                df.at[idx2, "Wedstrijden"] += 1

            df.at[idx1, "Totaal Punten"] += p1
            df.at[idx2, "Totaal Punten"] += p2

            df.at[idx1, "Totaal Beurten"] += beurten
            df.at[idx2, "Totaal Beurten"] += beurten

            matches.loc[len(matches)] = [
                str(d), per,
                s1, s2,
                h1, h2,
                c1, c2,
                beurten,
                winnaar,
                p1, p2
            ]

            df.to_csv(PLAYERS_FILE, index=False)
            matches.to_csv(MATCHES_FILE, index=False)

            st.success("Match opgeslagen")
            st.rerun()

# ======================
# RANKING
# ======================
elif menu == "🏆 Ranking":

    st.title("🏆 Ranking")

    ranking = df.copy()
    ranking["Moyenne"] = ranking["Totaal Punten"] / ranking["Totaal Beurten"].replace(0, 1)
    ranking["Handicap"] = (ranking["Moyenne"] * 25).round(2)

    st.dataframe(ranking.sort_values("Handicap", ascending=False), use_container_width=True)

# ======================
# 📊 STATS
# ======================
elif menu == "📊 Stats":

    st.title("📊 Stats")

    if len(matches) == 0:
        st.info("Geen data")
        st.stop()

    st.subheader("🏆 Meeste wins")
    st.dataframe(matches["Winnaar"].value_counts(), use_container_width=True)

# ======================
# 🧮 NIEUWE PAGINA: SPEELPUNTEN CALCULATOR
# ======================
elif menu == "🧮 Speelpunten calculator":

    st.title("🧮 Speelpunten calculator")

    col1, col2 = st.columns(2)

    with col1:
        gemaakt = st.number_input("Gemaakte punten", min_value=0)

    with col2:
        beurten = st.number_input("Beurten gespeeld", min_value=1)

    resultaat = speelpunten(gemaakt, beurten)

    st.success(f"🎯 Speelpunten: {resultaat}")

# ======================
# 👑 KAMPIOENSCHAP
# ======================
elif menu == "👑 Kampioenschap":

    st.title("👑 Kampioenschap")

    spelers = set(matches["Speler1"]).union(set(matches["Speler2"]))

    data = []

    for s in spelers:
        totaal = (
            matches[matches["Speler1"] == s]["Punten1"].sum() +
            matches[matches["Speler2"] == s]["Punten2"].sum()
        )

        data.append({"Speler": s, "Totaal": totaal})

    dfk = pd.DataFrame(data).sort_values("Totaal", ascending=False)

    st.success(f"🏆 Kampioen: {dfk.iloc[0]['Speler']}")
    st.dataframe(dfk, use_container_width=True)
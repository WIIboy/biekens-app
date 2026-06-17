import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

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
        "Speler", "H1_Handicap", "H2_Handicap",
        "Wedstrijden", "Totaal Punten", "Totaal Beurten"
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
# SAFE NUMERIC FIX
# ======================
def to_num(x):
    try:
        return float(x)
    except:
        return 0.0

for col in ["Wedstrijden", "Totaal Punten", "Totaal Beurten"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col in ["Beurten", "Punten1", "Punten2"]:
    if col in matches.columns:
        matches[col] = pd.to_numeric(matches[col], errors="coerce").fillna(0)

# ======================
# STYLE (groen + goud)
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
    return max(0.2, 10 - (beurten - 1) * 0.2)

def punten_verlies(p_win, car, handicap):
    if handicap == 0:
        return 0
    return round(p_win * car / handicap, 3)

def periode(d):
    m = pd.to_datetime(d).month
    return "H1" if m <= 6 else "H2"

def save():
    df.to_csv(PLAYERS_FILE, index=False)
    matches.to_csv(MATCHES_FILE, index=False)

# ======================
# H1 RULE (alleen stijgen)
# ======================
def update_h1(old, new):
    return max(old, new)

# ======================
# H2 RULE (vrij)
# ======================
def update_h2(new):
    return new

# ======================
# MENU
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🎮 Match",
    "🏆 Ranking",
    "📊 Stats",
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
    col3.metric("Punten", int(df["Totaal Punten"].sum()))

# ======================
# SPELERS
# ======================
elif menu == "👤 Spelers":
    st.title("👤 Spelers")

    naam = st.text_input("Nieuwe speler")

    if st.button("Toevoegen"):
        if naam:
            df.loc[len(df)] = [naam, 0, 0, 0, 0, 0]
            save()
            st.rerun()

    st.divider()

    if len(df) > 0:
        speler = st.selectbox("Verwijder speler", df["Speler"])

        if st.button("Verwijderen"):
            df = df[df["Speler"] != speler]
            matches = matches[(matches["Speler1"] != speler) & (matches["Speler2"] != speler)]
            save()
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

        h1 = st.number_input("Handicap 1", 1)
        h2 = st.number_input("Handicap 2", 1)

        c1 = st.number_input("Caramboles 1", 0)
        c2 = st.number_input("Caramboles 2", 0)

        beurten = st.number_input("Beurten", 1)
        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan"):
            idx1 = df.index[df["Speler"] == s1][0]
            idx2 = df.index[df["Speler"] == s2][0]

            p_win = punten_win(beurten)

            if winnaar == s1:
                p1 = p_win
                p2 = punten_verlies(p_win, c2, h2)
                df.at[idx1, "Wedstrijden"] += 1
            else:
                p2 = p_win
                p1 = punten_verlies(p_win, c1, h1)
                df.at[idx2, "Wedstrijden"] += 1

            df.at[idx1, "Totaal Punten"] += p1
            df.at[idx2, "Totaal Punten"] += p2
            df.at[idx1, "Totaal Beurten"] += beurten
            df.at[idx2, "Totaal Beurten"] += beurten

            # MATCH OPSLAAN
            matches.loc[len(matches)] = [
                str(d),
                periode(d),
                s1, s2,
                h1, h2,
                c1, c2,
                beurten,
                winnaar,
                p1, p2
            ]

            save()
            st.success("Match opgeslagen")
            st.rerun()

# ======================
# RANKING + H1/H2 HANDICAP LOGICA
# ======================
elif menu == "🏆 Ranking":
    st.title("🏆 Ranking")

    ranking = df.copy()

    ranking["Moyenne"] = ranking["Totaal Punten"] / ranking["Totaal Beurten"].replace(0, 1)
    ranking["Handicap"] = (ranking["Moyenne"] * 25).round().astype(int)

    st.dataframe(ranking.sort_values("Handicap", ascending=False))

# ======================
# STATS
# ======================
elif menu == "📊 Stats":
    st.title("📊 Stats")

    if len(matches) == 0:
        st.info("Geen data")
        st.stop()

    st.subheader("Wins")
    st.dataframe(matches["Winnaar"].value_counts())

    kortste = matches.loc[matches["Beurten"].idxmin()]

    st.subheader("Kortste match")
    st.dataframe(pd.DataFrame([kortste]))

# ======================
# KAMPIOENSCHAP
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
    st.dataframe(dfk)
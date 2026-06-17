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
# SAFE SAVE FUNCTION (BELANGRIJK)
# ======================
def safe_save(df, path):
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)

# ======================
# INIT FILES
# ======================
if not os.path.exists(PLAYERS_FILE):
    pd.DataFrame(columns=[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten"
    ]).to_csv(PLAYERS_FILE, index=False, encoding='utf-8')

if not os.path.exists(MATCHES_FILE):
    pd.DataFrame(columns=[
        "Datum", "Periode",
        "Speler1", "Speler2",
        "Handicap1", "Handicap2",
        "Caramboles1", "Caramboles2",
        "Beurten",
        "Winnaar",
        "Punten1", "Punten2"
    ]).to_csv(MATCHES_FILE, index=False, encoding='utf-8')

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

for col in ["Totaal Punten", "Totaal Beurten", "Wedstrijden"]:
    if col in df.columns:
        df[col] = df[col].apply(to_num)

# ======================
# FUNCTIONS
# ======================
def punten_win(beurten):
    return max(0.2, 10 - (beurten - 1) * 0.2)

def punten_verlies(p_win, car, handicap):
    if handicap == 0:
        return 0
    return round(p_win * car / handicap, 3)

def periode(datum):
    m = pd.to_datetime(datum).month
    return "H1" if m <= 6 else "H2"

# ======================
# MENU
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🎮 Match invoeren",
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
    col3.metric("Totaal punten", int(df["Totaal Punten"].sum()))

# ======================
# 👤 SPELERS
# ======================
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

                safe_save(df, PLAYERS_FILE)
                st.success("Toegevoegd")
                st.rerun()

    st.divider()

    st.subheader("🗑️ Speler verwijderen")

    if len(df) > 0:
        speler_del = st.selectbox("Selecteer speler", df["Speler"])

        if st.button("Verwijder speler"):
            df = df[df["Speler"] != speler_del]

            matches = matches[
                (matches["Speler1"] != speler_del) &
                (matches["Speler2"] != speler_del)
            ]

            safe_save(df, PLAYERS_FILE)
            safe_save(matches, MATCHES_FILE)

            st.success("Speler verwijderd")
            st.rerun()

# ======================
# 🎮 MATCH INVOER (MET DATUM)
# ======================
elif menu == "🎮 Match invoeren":
    st.title("🎮 Match invoeren")

    if len(df) > 0:
        s1 = st.selectbox("Speler 1", df["Speler"], key="s1")
        s2 = st.selectbox("Speler 2", df[df["Speler"] != s1]["Speler"], key="s2")

        match_date = st.date_input("Datum match", value=date.today())

        h1 = st.number_input("Handicap 1", min_value=1, value=1)
        h2 = st.number_input("Handicap 2", min_value=1, value=1)

        c1 = st.number_input("Caramboles speler 1", min_value=0, value=0)
        c2 = st.number_input("Caramboles speler 2", min_value=0, value=0)

        beurten = st.number_input("Beurten winnaar", min_value=1, value=1)

        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan match"):
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

            df.at[idx1, "Totaal Punten"] = to_num(df.at[idx1, "Totaal Punten"]) + p1
            df.at[idx2, "Totaal Punten"] = to_num(df.at[idx2, "Totaal Punten"]) + p2

            df.at[idx1, "Totaal Beurten"] = to_num(df.at[idx1, "Totaal Beurten"]) + beurten
            df.at[idx2, "Totaal Beurten"] = to_num(df.at[idx2, "Totaal Beurten"]) + beurten

            safe_save(df, PLAYERS_FILE)

            new_match = pd.DataFrame([{
                "Datum": str(match_date),
                "Periode": periode(match_date),
                "Speler1": s1,
                "Speler2": s2,
                "Handicap1": h1,
                "Handicap2": h2,
                "Caramboles1": c1,
                "Caramboles2": c2,
                "Beurten": beurten,
                "Winnaar": winnaar,
                "Punten1": p1,
                "Punten2": p2
            }])

            matches = pd.concat([matches, new_match], ignore_index=True)
            safe_save(matches, MATCHES_FILE)

            st.success("Match opgeslagen")
            st.rerun()
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
# 🎨 CLUB THEME (GROEN + GEEL)
# ======================
st.markdown("""
<style>

/* MAIN BACKGROUND - biljartlaken groen */
.stApp {
    background: radial-gradient(circle at top, #0b3d2e, #061a14 75%);
    color: #f5f5f5;
}

/* TITLES */
h1 {
    color: #d4af37 !important;
    font-weight: 900;
}

h2, h3 {
    color: #f5d77b !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #07261c;
}

/* BUTTONS (goud accent) */
.stButton>button {
    background: linear-gradient(135deg, #d4af37, #b9972d);
    color: black;
    font-weight: 700;
    border-radius: 10px;
    border: none;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #f5d77b, #d4af37);
    transform: scale(1.03);
}

/* INPUTS */
input, .stSelectbox, .stNumberInput {
    border-radius: 8px !important;
}

/* METRICS (HOME CARDS) */
[data-testid="stMetric"] {
    background: rgba(212,175,55,0.08);
    border: 1px solid rgba(212,175,55,0.25);
    padding: 14px;
    border-radius: 12px;
}

/* TABLE STYLE */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid rgba(212,175,55,0.25);
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)

# ======================
# FILES
# ======================
PLAYERS_FILE = "spelers.csv"
MATCHES_FILE = "wedstrijden.csv"

def safe_save(df, path):
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)

# ======================
# INIT FILES
# ======================
if not os.path.exists(PLAYERS_FILE):
    pd.DataFrame(columns=[
        "Speler", "Wedstrijden", "Totaal Punten", "Totaal Beurten"
    ]).to_csv(PLAYERS_FILE, index=False)

if not os.path.exists(MATCHES_FILE):
    pd.DataFrame(columns=[
        "Datum", "Periode",
        "Speler1", "Speler2",
        "Handicap1", "Handicap2",
        "Caramboles1", "Caramboles2",
        "Beurten", "Winnaar",
        "Punten1", "Punten2"
    ]).to_csv(MATCHES_FILE, index=False)

df = pd.read_csv(PLAYERS_FILE)
matches = pd.read_csv(MATCHES_FILE)

# ======================
# NUMERIC FIX
# ======================
def to_num(x):
    try:
        return float(x)
    except:
        return 0.0

for col in ["Wedstrijden", "Totaal Punten", "Totaal Beurten"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col in ["Beurten", "Punten1", "Punten2"]:
    matches[col] = pd.to_numeric(matches[col], errors="coerce").fillna(0)

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
    col1.metric("👤 Spelers", len(df))
    col2.metric("🎮 Wedstrijden", len(matches))
    col3.metric("🏆 Punten", int(df["Totaal Punten"].sum()))

# ======================
# SPELERS
# ======================
elif menu == "👤 Spelers":
    st.title("👤 Spelersbeheer")

    naam = st.text_input("Nieuwe speler")

    if st.button("➕ Toevoegen"):
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

    st.subheader("🗑️ Verwijderen")

    if len(df) > 0:
        speler_del = st.selectbox("Selecteer speler", df["Speler"])

        if st.button("❌ Verwijder"):
            df = df[df["Speler"] != speler_del]
            matches = matches[(matches["Speler1"] != speler_del) & (matches["Speler2"] != speler_del)]

            safe_save(df, PLAYERS_FILE)
            safe_save(matches, MATCHES_FILE)

            st.success("Speler verwijderd")
            st.rerun()

# ======================
# MATCH INVOER
# ======================
elif menu == "🎮 Match invoeren":
    st.title("🎮 Match invoeren")

    if len(df) > 0:
        s1 = st.selectbox("Speler 1", df["Speler"], key="s1")
        s2 = st.selectbox("Speler 2", df[df["Speler"] != s1]["Speler"], key="s2")

        match_date = st.date_input("📅 Datum", value=date.today())

        h1 = st.number_input("Handicap 1", min_value=1, value=1)
        h2 = st.number_input("Handicap 2", min_value=1, value=1)

        c1 = st.number_input("Caramboles 1", min_value=0, value=0)
        c2 = st.number_input("Caramboles 2", min_value=0, value=0)

        beurten = st.number_input("Beurten winnaar", min_value=1, value=1)

        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("💾 Opslaan"):
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
import streamlit as st
import pandas as pd
import json
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="🎱 K.B.C. De Biekens",
    page_icon="🎱",
    layout="wide"
)

# ======================
# GOOGLE SHEETS CONNECT
# ======================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

info = json.loads(st.secrets["gcp_service_account"]["json_key"])
creds = Credentials.from_service_account_info(info, scopes=scope)

client = gspread.authorize(creds)

spreadsheet = client.open_by_key("1o-llMtZRjt9EN1ZF_D7ITtLJCq3CG_1lDXhprRSrZgw")

ws_players = spreadsheet.worksheet("Spelers")
ws_matches = spreadsheet.worksheet("Wedstrijden")

# ======================
# SAFE LOAD (BELANGRIJK FIX)
# ======================
def load_players():
    df = pd.DataFrame(ws_players.get_all_records())

    if df.empty:
        df = pd.DataFrame(columns=[
            "Speler", "Wedstrijden", "Totaal Punten", "Totaal Beurten", "Handicap"
        ])

    # 🔥 HARD FIX: alles numeriek maken
    num_cols = ["Wedstrijden", "Totaal Punten", "Totaal Beurten", "Handicap"]

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def save_players(df):
    ws_players.clear()
    ws_players.update([df.columns.tolist()] + df.values.tolist())


def load_matches():
    df = pd.DataFrame(ws_matches.get_all_records())
    return df.fillna(0)


def save_matches(df):
    ws_matches.clear()
    ws_matches.update([df.columns.tolist()] + df.values.tolist())

df = load_players()
matches = load_matches()

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
# FORMULES
# ======================
def bereken_nieuw_punten(punten, beurten):
    return round((punten / beurten) * 25, 3)

def punten_win(beurten):
    return round(max(0.2, 10 - (beurten - 1) * 0.2), 2)

# 🔥 SAFE GET (BELANGRIJK)
def get_num(row, col):
    try:
        return float(row[col])
    except:
        return 0.0

def update_player(speler, punten_toevoeging, beurten_toevoeging, wedstrijd_win=False):
    global df

    idx = df.index[df["Speler"] == speler][0]

    # huidige waarden veilig ophalen
    huidige_punten = get_num(df.loc[idx], "Totaal Punten")
    huidige_beurten = get_num(df.loc[idx], "Totaal Beurten")
    huidige_wedstrijden = get_num(df.loc[idx], "Wedstrijden")

    # updates
    df.loc[idx, "Totaal Punten"] = huidige_punten + punten_toevoeging
    df.loc[idx, "Totaal Beurten"] = huidige_beurten + beurten_toevoeging

    if wedstrijd_win:
        df.loc[idx, "Wedstrijden"] = huidige_wedstrijden + 1

    # handicap herberekenen
    if (huidige_beurten + beurten_toevoeging) > 0:
        df.loc[idx, "Handicap"] = bereken_nieuw_punten(
            df.loc[idx, "Totaal Punten"],
            df.loc[idx, "Totaal Beurten"]
        )
    else:
        df.loc[idx, "Handicap"] = 0

# ======================
# MENU
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🎮 Match",
    "🏆 Ranking",
    "👑 Kampioenschap",
    "🧮 Handicap"
])

# ======================
# HOME
# ======================
if menu == "🏠 Home":
    st.title("🎱 K.B.C. De Biekens")
    st.metric("Spelers", len(df))
    st.metric("Wedstrijden", len(matches))

# ======================
# SPELERS
# ======================
elif menu == "👤 Spelers":

    st.title("👤 Spelersbeheer")

    naam = st.text_input("Nieuwe speler")

    if st.button("Toevoegen"):
        if naam:
            if naam.lower() not in df["Speler"].astype(str).str.lower().values:
                df.loc[len(df)] = [naam, 0, 0, 0, 0]
                save_players(df)
                st.rerun()

# ======================
# MATCH
# ======================
elif menu == "🎮 Match":

    st.title("🎮 Match invoeren")

    if len(df) > 1:

        s1 = st.selectbox("Speler 1", df["Speler"])
        s2 = st.selectbox("Speler 2", df[df["Speler"] != s1]["Speler"])

        h1 = st.number_input("Handicap 1", 1)
        h2 = st.number_input("Handicap 2", 1)

        c1 = st.number_input("Caramboles 1", 0)
        c2 = st.number_input("Caramboles 2", 0)

        beurten = st.number_input("Beurten", 1)
        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan"):

            p_win = punten_win(beurten)

            p1 = p_win if winnaar == s1 else 0
            p2 = p_win if winnaar == s2 else 0

            update_player(s1, p1, beurten, winnaar == s1)
            update_player(s2, p2, beurten, winnaar == s2)

            save_players(df)

            matches.loc[len(matches)] = [
                str(date.today()),
                s1, s2, h1, h2, c1, c2, beurten, winnaar, p1, p2
            ]

            save_matches(matches)

            st.success("Match opgeslagen")
            st.rerun()

# ======================
# RANKING
# ======================
elif menu == "🏆 Ranking":

    st.title("🏆 Ranking")
    st.dataframe(df.sort_values("Handicap", ascending=False))

# ======================
# HANDICAP
# ======================
elif menu == "🧮 Handicap":

    st.title("🧮 Handicap berekening")

    speler = st.selectbox("Kies speler", df["Speler"])
    r = df[df["Speler"] == speler].iloc[0]

    st.metric("Handicap", r["Handicap"])
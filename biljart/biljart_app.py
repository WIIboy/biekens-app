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
# GOOGLE SHEETS
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
# MATCH SCHEMA
# ======================
MATCH_COLUMNS = [
    "Datum",
    "Speler1",
    "Speler2",
    "Handicap1",
    "Handicap2",
    "Caramboles1",
    "Caramboles2",
    "Beurten",
    "Winnaar",
    "Punten1",
    "Punten2"
]

PLAYER_COLUMNS = [
    "Speler",
    "Wedstrijden",
    "Totaal Punten",
    "Totaal Beurten",
    "Handicap"
]

# ======================
# LOAD PLAYERS
# ======================
def load_players():
    df = pd.DataFrame(ws_players.get_all_records())

    if df.empty:
        df = pd.DataFrame(columns=PLAYER_COLUMNS)

    for col in PLAYER_COLUMNS[1:]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# ======================
# LOAD MATCHES
# ======================
def load_matches():
    df = pd.DataFrame(ws_matches.get_all_records())

    if df.empty:
        df = pd.DataFrame(columns=MATCH_COLUMNS)

    return df

def save_players(df):
    ws_players.clear()
    ws_players.update([df.columns.tolist()] + df.values.tolist())

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
def handicap(punten, beurten):
    return round((punten / beurten) * 25, 3) if beurten > 0 else 0

def punten_win(beurten):
    return round(max(0.2, 10 - (beurten - 1) * 0.2), 2)

# ======================
# SAFE PLAYER UPDATE
# ======================
def update_player(speler, punten, beurten, win=False):
    global df

    idx = df.index[df["Speler"] == speler][0]

    w = float(df.at[idx, "Wedstrijden"])
    p = float(df.at[idx, "Totaal Punten"])
    b = float(df.at[idx, "Totaal Beurten"])

    if win:
        w += 1

    p += float(punten)
    b += float(beurten)

    df.at[idx, "Wedstrijden"] = w
    df.at[idx, "Totaal Punten"] = p
    df.at[idx, "Totaal Beurten"] = b
    df.at[idx, "Handicap"] = handicap(p, b)

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

            new_match = pd.DataFrame([[
                str(date.today()),
                s1, s2, h1, h2, c1, c2, beurten, winnaar, p1, p2
            ]], columns=MATCH_COLUMNS)

            matches = pd.concat([matches, new_match], ignore_index=True)

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
# KAMPIOENSCHAP
# ======================
elif menu == "👑 Kampioenschap":

    st.title("👑 Kampioenschap")

    if len(matches) > 0:

        spelers = set(matches["Speler1"]).union(set(matches["Speler2"]))

        data = []

        for s in spelers:

            totaal = (
                matches[matches["Speler1"] == s]["Punten1"].sum() +
                matches[matches["Speler2"] == s]["Punten2"].sum()
            )

            data.append({
                "Speler": s,
                "Totaal": totaal
            })

        dfk = pd.DataFrame(data).sort_values("Totaal", ascending=False)

        st.dataframe(dfk)

# ======================
# HANDICAP CALCULATOR
# ======================
elif menu == "🧮 Handicap":

    st.title("🧮 Handicap berekening")

    if len(df) > 0:
        speler = st.selectbox("Kies speler", df["Speler"])

    punten = st.number_input("Totaal gemaakte punten", min_value=0.0, step=0.01)
    beurten = st.number_input("Totaal gespeelde beurten", min_value=1)

    if beurten > 0:
        result = round((punten / beurten) * 25, 3)
        st.success(f"Nieuw handicap punt voor **{speler}**: **{result}**")
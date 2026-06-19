import streamlit as st
import pandas as pd
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

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

SPREADSHEET_NAME = "Biekens Data"  # 👈 PAS DIT AAN NAAR JE ECHTE SHEET NAAM
spreadsheet = client.open(SPREADSHEET_NAME)

ws_players = spreadsheet.worksheet("Spelers")
ws_matches = spreadsheet.worksheet("Wedstrijden")


# ======================
# LOAD / SAVE SAFE
# ======================
def load_players():
    df = pd.DataFrame(ws_players.get_all_records())
    return df.fillna(0)

def save_players(df):
    df = df.copy()
    ws_players.clear()
    ws_players.update([df.columns.tolist()] + df.values.tolist())


def load_matches():
    df = pd.DataFrame(ws_matches.get_all_records())
    return df.fillna(0)

def save_matches(df):
    df = df.copy()
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
# BILJART PUNTEN
# ======================
def punten_win(beurten):
    return round(max(0.2, 10 - (beurten - 1) * 0.2), 2)

def handicap(punten, beurten):
    return round((punten / beurten) * 25, 3) if beurten > 0 else 0


# ======================
# MENU
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🎮 Match",
    "🏆 Ranking",
    "👑 Kampioenschap"
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
            if len(df) == 0 or naam.lower() not in df["Speler"].str.lower().values:
                df.loc[len(df)] = [naam, 0, 0, 0]
                save_players(df)
                st.success("Toegevoegd")
                st.rerun()
            else:
                st.warning("Speler bestaat al")

    st.divider()

    if len(df) > 0:

        del_speler = st.selectbox("Verwijder speler", df["Speler"])

        if st.button("Verwijderen"):
            df = df[df["Speler"] != del_speler]
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

            idx1 = df.index[df["Speler"] == s1][0]
            idx2 = df.index[df["Speler"] == s2][0]

            p_win = punten_win(beurten)

            p1 = p_win if winnaar == s1 else 0
            p2 = p_win if winnaar == s2 else 0

            df.at[idx1, "Wedstrijden"] += 1 if winnaar == s1 else 0
            df.at[idx2, "Wedstrijden"] += 1 if winnaar == s2 else 0

            df.at[idx1, "Totaal Punten"] += p1
            df.at[idx2, "Totaal Punten"] += p2

            df.at[idx1, "Totaal Beurten"] += beurten
            df.at[idx2, "Totaal Beurten"] += beurten

            save_players(df)

            matches.loc[len(matches)] = [
                str(date.today()),
                s1,
                s2,
                h1,
                h2,
                c1,
                c2,
                beurten,
                winnaar,
                p1,
                p2
            ]

            save_matches(matches)

            st.success("Match opgeslagen")
            st.rerun()


# ======================
# RANKING
# ======================
elif menu == "🏆 Ranking":

    st.title("🏆 Ranking")

    if len(df) > 0:

        df["Handicap"] = df.apply(
            lambda r: handicap(r["Totaal Punten"], r["Totaal Beurten"]),
            axis=1
        )

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
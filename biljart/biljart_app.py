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
# SAFE LOAD (BELANGRIJK FIX)
# ======================
def load_data():
    df = pd.read_csv(PLAYERS_FILE)
    matches = pd.read_csv(MATCHES_FILE)

    for col in ["Wedstrijden", "Totaal Punten", "Totaal Beurten"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["Beurten", "Punten1", "Punten2"]:
        if col in matches.columns:
            matches[col] = pd.to_numeric(matches[col], errors="coerce").fillna(0)

    return df, matches

df, matches = load_data()

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
        "Beurten",
        "Winnaar",
        "Punten1", "Punten2"
    ]).to_csv(MATCHES_FILE, index=False)

# ======================
# THEME (simpel groen/geel stabiel)
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
    return "H1" if pd.to_datetime(d).month <= 6 else "H2"

def save():
    df.to_csv(PLAYERS_FILE, index=False)
    matches.to_csv(MATCHES_FILE, index=False)

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
            df.loc[len(df)] = [naam, 0, 0, 0]
            save()
            st.rerun()

    st.divider()

    if len(df) > 0:
        speler = st.selectbox("Verwijder speler", df["Speler"])

        if st.button("Verwijderen"):
            df.drop(df[df["Speler"] == speler].index, inplace=True)
            matches.drop(matches[(matches["Speler1"] == speler) | (matches["Speler2"] == speler)].index, inplace=True)
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

        date_match = st.date_input("Datum", value=date.today())

        h1 = st.number_input("Handicap 1", 1)
        h2 = st.number_input("Handicap 2", 1)

        c1 = st.number_input("Caramboles 1", 0)
        c2 = st.number_input("Caramboles 2", 0)

        beurten = st.number_input("Beurten", 1)
        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan"):
            idx1 = df[df["Speler"] == s1].index[0]
            idx2 = df[df["Speler"] == s2].index[0]

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

            new = pd.DataFrame([{
                "Datum": str(date_match),
                "Periode": periode(date_match),
                "Speler1": s1,
                "Speler2": s2,
                "Winnaar": winnaar,
                "Beurten": beurten,
                "Punten1": p1,
                "Punten2": p2
            }])

            matches = pd.concat([matches, new], ignore_index=True)
            save()

            st.success("Opgeslagen")
            st.rerun()

# ======================
# RANKING (FIXED)
# ======================
elif menu == "🏆 Ranking":
    st.title("🏆 Ranking")

    ranking = df.copy()
    ranking["Moyenne"] = ranking.apply(
        lambda r: r["Totaal Punten"] / r["Totaal Beurten"] if r["Totaal Beurten"] > 0 else 0,
        axis=1
    )

    ranking["Handicap"] = (ranking["Moyenne"] * 25).round().astype(int)
    ranking = ranking.sort_values("Handicap", ascending=False)

    st.dataframe(ranking, use_container_width=True)

# ======================
# STATS (FIXED)
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
# KAMPIOENSCHAP (FIXED)
# ======================
elif menu == "👑 Kampioenschap":
    st.title("👑 Kampioenschap")

    if len(matches) == 0:
        st.info("Geen data beschikbaar")
        st.stop()

    spelers = set(matches["Speler1"]).union(set(matches["Speler2"]))

    data = []

    for s in spelers:
        totaal = (
            matches[matches["Speler1"] == s]["Punten1"].sum() +
            matches[matches["Speler2"] == s]["Punten2"].sum()
        )

        data.append({
            "Speler": s,
            "Totaal": float(totaal)
        })

    dfk = pd.DataFrame(data)

    if dfk.empty:
        st.info("Geen kampioenschapsdata")
        st.stop()

    dfk = dfk.sort_values("Totaal", ascending=False).reset_index(drop=True)

    # ======================
    # 🏅 PODIUM
    # ======================
    st.subheader("🏆 Podium")

    cols = st.columns(3)

    if len(dfk) > 0:
        cols[1].metric("🥇 1e plaats", dfk.iloc[0]["Speler"], f"{dfk.iloc[0]['Totaal']:.2f}")

    if len(dfk) > 1:
        cols[0].metric("🥈 2e plaats", dfk.iloc[1]["Speler"], f"{dfk.iloc[1]['Totaal']:.2f}")

    if len(dfk) > 2:
        cols[2].metric("🥉 3e plaats", dfk.iloc[2]["Speler"], f"{dfk.iloc[2]['Totaal']:.2f}")

    st.divider()

    # ======================
    # 📊 VOLLEDIGE RANKING
    # ======================
    st.subheader("📊 Volledige ranking")

    st.dataframe(
        dfk,
        use_container_width=True,
        hide_index=True
    )
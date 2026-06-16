import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
# INIT PLAYERS
# ======================
if not os.path.exists(PLAYERS_FILE):
    pd.DataFrame(columns=[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten"
    ]).to_csv(PLAYERS_FILE, index=False)

# ======================
# INIT MATCHES
# ======================
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

h2, h3 {
    color: #f5d77b !important;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HANDICAP SYSTEM
# ======================
def bereken_handicap(row):
    if row["Totaal Beurten"] > 0:
        moyenne = row["Totaal Punten"] / row["Totaal Beurten"]
    else:
        moyenne = 0
    return round(moyenne * 25), moyenne

# ======================
# REGLEMENT
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
# SIDEBAR
# ======================
menu = st.sidebar.radio("📊 Menu", [
    "🏠 Home",
    "👤 Spelers",
    "🏆 Ranking",
    "📊 Stats",
    "👑 Kampioenschap"
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

    st.subheader("🗑️ Speler verwijderen")

    if len(df) > 0:
        speler_del = st.selectbox("Selecteer speler", df["Speler"])

        if st.button("Verwijder speler"):
            df = df[df["Speler"] != speler_del]
            df.to_csv(PLAYERS_FILE, index=False)

            matches = matches[
                (matches["Speler1"] != speler_del) &
                (matches["Speler2"] != speler_del)
            ]
            matches.to_csv(MATCHES_FILE, index=False)

            st.success(f"{speler_del} werd verwijderd.")
            st.rerun()

    st.divider()

    st.subheader("🎮 Match invoeren")

    if len(df) > 0:
        s1 = st.selectbox("Speler 1", df["Speler"])
        s2 = st.selectbox("Speler 2", df["Speler"])

        h1 = st.number_input("Handicap 1", min_value=1, value=1)
        h2 = st.number_input("Handicap 2", min_value=1, value=1)

        c1 = st.number_input("Caramboles speler 1", min_value=0, value=0)
        c2 = st.number_input("Caramboles speler 2", min_value=0, value=0)

        beurten = st.number_input("Beurten winnaar", min_value=1, value=1)

        winnaar = st.selectbox("Winnaar", [s1, s2])

        if st.button("Opslaan match"):
            idx1 = df[df["Speler"] == s1].index[0]
            idx2 = df[df["Speler"] == s2].index[0]

            p_win = punten_win(beurten)

            if winnaar == s1:
                p1 = p_win
                p2 = punten_verlies(p_win, c2, h2)
                df.loc[idx1, "Wedstrijden"] += 1
            else:
                p2 = p_win
                p1 = punten_verlies(p_win, c1, h1)
                df.loc[idx2, "Wedstrijden"] += 1

            df.loc[idx1, "Totaal Punten"] += p1
            df.loc[idx2, "Totaal Punten"] += p2

            df.loc[idx1, "Totaal Beurten"] += beurten
            df.loc[idx2, "Totaal Beurten"] += beurten

            df.to_csv(PLAYERS_FILE, index=False)

            new_match = pd.DataFrame([{
                "Datum": datetime.now().date(),
                "Periode": periode(datetime.now()),
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
            matches.to_csv(MATCHES_FILE, index=False)

            st.success("Match opgeslagen")
            st.rerun()

# =========================================================
# RANKING (AANGEPAST)
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

    # 🔥 BELANGRIJK: enkel spelers ranking tonen
    ranking = ranking[[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten",
        "Moyenne",
        "Handicap"
    ]]

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# STATS
# =========================================================
elif menu == "📊 Stats":
    st.title("📊 Statistieken")

    if len(matches) == 0:
        st.info("Geen data")
        st.stop()

    st.subheader("🏆 Meeste wins")
    st.dataframe(matches["Winnaar"].value_counts(), use_container_width=True)

    kortste = matches.loc[matches["Beurten"].idxmin()]

    st.markdown("### ⚡ Kortste partij")

    st.markdown(f"""
**🎱 Speler 1:** {kortste['Speler1']}  
**🎱 Speler 2:** {kortste['Speler2']}  
**🎯 Beurten:** {kortste['Beurten']}  
**🏆 Winnaar:** {kortste['Winnaar']}  
**📊 Punten speler 1:** {kortste['Punten1']}  
**📊 Punten speler 2:** {kortste['Punten2']}  
""")

# =========================================================
# KAMPIOENSCHAP
# =========================================================
elif menu == "👑 Kampioenschap":
    st.title("👑 Kampioenschap")

    if len(matches) == 0:
        st.info("Geen data")
        st.stop()

    spelers = set(matches["Speler1"]).union(set(matches["Speler2"]))

    data = []

    def totaal(df, speler):
        return df[df["Speler1"] == speler]["Punten1"].sum() + \
               df[df["Speler2"] == speler]["Punten2"].sum()

    for s in spelers:
        h1 = matches[matches["Periode"] == "H1"]
        h2 = matches[matches["Periode"] == "H2"]

        data.append({
            "Speler": s,
            "H1": totaal(h1, s),
            "H2": totaal(h2, s),
            "Totaal": totaal(matches, s)
        })

    df_kamp = pd.DataFrame(data).fillna(0)
    df_kamp = df_kamp.sort_values("Totaal", ascending=False)

    st.success(f"🏆 Kampioen: {df_kamp.iloc[0]['Speler']}")

    st.dataframe(df_kamp, use_container_width=True)
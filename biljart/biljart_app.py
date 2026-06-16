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
# 🔥 FIX: force numeric types (BELANGRIJK)
# ======================
numeric_cols = ["Totaal Punten", "Totaal Beurten", "Wedstrijden"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

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

    ranking = ranking[[
        "Speler",
        "Wedstrijden",
        "Totaal Punten",
        "Totaal Beurten",
        "Moyenne",
        "Handicap"
    ]]

    st.dataframe(ranking, use_container_width=True, hide_index=True)

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

    def totaal(df_, speler):
        return df_[df_["Speler1"] == speler]["Punten1"].sum() + \
               df_[df_["Speler2"] == speler]["Punten2"].sum()

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
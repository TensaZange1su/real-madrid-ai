
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Real Madrid AI Transfer Intelligence", page_icon="⚽", layout="wide")
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

team = pd.read_csv(DATA / "team_season_stats.csv")
players = pd.read_csv(DATA / "players.csv")
player_stats = pd.read_csv(DATA / "player_season_stats.csv")
sources = pd.read_csv(DATA / "source_register.csv")

st.sidebar.title("REAL MADRID · AI")
page = st.sidebar.radio("Navigation", [
    "Overview", "Season Analysis", "Squad & Players",
    "Scouting & Candidates", "Budget Optimizer", "Data Quality & Sources"
])
st.sidebar.caption("Research: 2023/24–2025/26 · Planning: 2026/27")
budget = st.sidebar.number_input("Transfer budget (€M)", min_value=0, max_value=500, value=200, step=5)

st.title("Real Madrid AI Transfer Intelligence")
st.caption("Decision-support prototype · unified player model · evidence-first workflow")

if page == "Overview":
    st.info("Prototype status: team-level La Liga results are populated. The player-season panel is a schema scaffold with provisional Yan Diomande records pending verification. No ML recommendation is active yet.")
    latest, prev = team.iloc[-1], team.iloc[-2]
    cols = st.columns(4)
    cols[0].metric("2025/26 points", int(latest.points), int(latest.points-prev.points))
    cols[1].metric("Goals scored", int(latest.goals_for), int(latest.goals_for-prev.goals_for))
    cols[2].metric("Goals conceded", int(latest.goals_against), int(latest.goals_against-prev.goals_against))
    cols[3].metric("Transfer budget", f"€{budget}M")
    long = team.melt(id_vars="season", value_vars=["points","goals_for","goals_against"], var_name="metric", value_name="value")
    long["metric"] = long.metric.map({"points":"Points","goals_for":"Goals scored","goals_against":"Goals conceded"})
    st.plotly_chart(px.line(long, x="season", y="value", color="metric", markers=True, title="Three-season La Liga trajectory"), use_container_width=True)
    st.dataframe(team, use_container_width=True, hide_index=True)

elif page == "Season Analysis":
    st.subheader("Team performance by season · La Liga")
    selected = st.multiselect("Seasons", team.season.tolist(), default=team.season.tolist())
    view = team[team.season.isin(selected)]
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(view, x="season", y=["wins","draws","losses"], barmode="group", title="Wins / draws / losses"), use_container_width=True)
    c2.plotly_chart(px.bar(view, x="season", y=["goals_for","goals_against"], barmode="group", title="Goals for / against"), use_container_width=True)
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption("Descriptive association only; this does not identify causes of performance changes.")

elif page == "Squad & Players":
    st.subheader("Unified player database")
    st.write("Every player belongs in one canonical player dimension. Player histories are stored as multiple season/club/competition rows in the same fact table.")
    st.dataframe(players, use_container_width=True, hide_index=True)
    st.subheader("Player-season performance")
    st.dataframe(player_stats, use_container_width=True, hide_index=True)
    st.warning("Yan Diomande is included in the same canonical player table and player-season fact table as every other player.")

elif page == "Scouting & Candidates":
    st.subheader("AI scouting workspace")
    st.info("Candidate ranking is intentionally disabled until player metrics, positions, minutes, competition context and market values are ingested and validated.")
    st.markdown("""
    Planned scoring dimensions:
    - Tactical fit by position and role
    - Position-normalized performance per 90
    - Age and development trajectory
    - Availability and injury-risk indicators (only if sourced)
    - Estimated fee and wage affordability
    - Data confidence / sample-size penalty
    """)
    st.dataframe(player_stats, use_container_width=True, hide_index=True)

elif page == "Budget Optimizer":
    st.subheader("Scenario allocation — not a transfer recommendation")
    defense = st.slider("Defence (€M)", 0, budget, min(60, budget), 5)
    midfield = st.slider("Midfield (€M)", 0, budget, min(50, budget), 5)
    attack = st.slider("Attack (€M)", 0, budget, min(70, budget), 5)
    remainder = budget - defense - midfield - attack
    st.metric("Unallocated (€M)", remainder)
    if remainder < 0:
        st.error("Allocation exceeds the available budget.")
    else:
        st.success("Scenario is within the user-provided budget.")
    st.caption("This is a manual allocation sandbox. The optimization engine will be added after candidate and cost data are verified.")

elif page == "Data Quality & Sources":
    st.subheader("Source register")
    st.dataframe(sources, use_container_width=True, hide_index=True)
    st.subheader("Current gaps")
    st.markdown("""
    - Full player-season panel for all three seasons: not loaded.
    - Standard, shooting, passing, possession, defensive actions and playing-time tables: to ingest.
    - Transfer fees and market values: require dated snapshots and source confidence.
    - Wages and injury history: unavailable in current project data.
    - Yan Diomande's squad status and previous draft statistics: require verification.
    - Competition scopes must remain explicit; league totals cannot be compared directly with all-competition totals.
    """)
st.divider()
st.caption("Prototype v0.2 · Not an official Real Madrid product · No unsupported scouting recommendations")

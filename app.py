from pathlib import Path
from itertools import combinations
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Real Madrid | AI Football Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
REPORTS = ROOT / "reports"
EXTERNAL = DATA / "external"

st.markdown("""
<style>
.stApp {background:#0d131a;color:#f4f6f8}
[data-testid="stSidebar"] {background:#121d27}
[data-testid="stMetric"] {background:#17232e;border:1px solid #2a3b49;padding:13px 15px;border-radius:12px}
[data-testid="stMetricLabel"] {color:#b9c5cf}
[data-testid="stMetricValue"] {color:#f4f6f8}
h1,h2,h3 {color:#f4f6f8}
.small-note {color:#aab7c4;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Real Madrid — AI Football Intelligence")
st.caption("Squad intelligence · Player profiles · External scouting · Transfer scenario planning")
st.divider()

def first_existing(paths):
    return next((p for p in paths if p and Path(p).exists()), None)

def read_csv_optional(paths):
    path = first_existing(paths)
    if path is None:
        return pd.DataFrame(), None
    try:
        return pd.read_csv(path), path
    except Exception as exc:
        st.warning(f"Не удалось прочитать {Path(path).name}: {exc}")
        return pd.DataFrame(), path

def normalize_season(series):
    s = series.astype(str).str.strip().str.replace("-", "/", regex=False)
    return s.replace({"2324":"2023/24", "2425":"2024/25", "2526":"2025/26"})

def to_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def normalize_pos(value):
    if pd.isna(value): return "Unknown"
    v = str(value).upper()
    if "GK" in v or "KEEPER" in v: return "GK"
    if "FW" in v or "FORWARD" in v or "ATT" in v: return "FW"
    if "MF" in v or "MID" in v: return "MF"
    if "DF" in v or "DEF" in v: return "DF"
    return "Unknown"

def fmt_eur(x):
    return "—" if pd.isna(x) else f"€{x/1e6:.1f}m"

# Real Madrid historical squad
squad, squad_path = read_csv_optional([
    PROCESSED/"real_madrid_player_season_clean.csv",
    PROCESSED/"real_madrid_clean.csv",
    PROCESSED/"real_madrid_player_season_laliga_2023_2026_clean.csv",
    PROCESSED/"real_madrid_player_season_laliga_2023_2026.csv",
])

# Full external scouting universe and top-60 shortlist
scouting_pool, pool_path = read_csv_optional([
    PROCESSED/"external_scouting_pool_2025_26.csv",
    ROOT/"external_scouting_pool_2025_26.csv",
])
scouting, scouting_path = read_csv_optional([
    PROCESSED/"external_scouting_shortlist_2025_26.csv",
    REPORTS/"external_scouting_shortlist_2025_26.csv",
    REPORTS/"transfer_candidate_shortlist_2026_27.csv",
])
need, need_path = read_csv_optional([REPORTS/"transfer_position_priorities_2026_27.csv"])
ratings, ratings_path = read_csv_optional([
    PROCESSED/"real_madrid_player_ratings.csv",
    PROCESSED/"player_ratings.csv",
    REPORTS/"player_ratings.csv",
])
market_values, market_path = read_csv_optional([
    EXTERNAL/"market_values_2026_11.csv",
    ROOT/"market_values_2026_11.csv",
])
manifest_path = first_existing([REPORTS/"external_scouting_manifest.json"])
manifest = {}
if manifest_path:
    try: manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except Exception: pass
summary_path = first_existing([REPORTS/"transfer_optimizer_summary_2026_27.json"])
summary = {}
if summary_path:
    try: summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    except Exception: pass

# Normalize Real Madrid dataset
if not squad.empty:
    aliases = {
        "player_name":["player_name","player","name"], "season":["season"],
        "position":["position_group","position","pos"], "minutes":["minutes","playing_time_min","min"],
        "age":["age"], "goals":["goals","performance_gls","standard_gls"],
        "assists":["assists","performance_ast"],
        "goals_per_90":["goals_per_90","per_90_minutes_gls"],
        "assists_per_90":["assists_per_90","per_90_minutes_ast"],
        "goal_contributions_per_90":["goal_contributions_per_90","per_90_minutes_g_a"],
    }
    for target, candidates in aliases.items():
        if target not in squad.columns:
            src = next((c for c in candidates if c in squad.columns), None)
            if src: squad[target] = squad[src]
    if "season" in squad: squad["season"] = normalize_season(squad["season"])
    if "position" in squad: squad["position_group"] = squad["position"].apply(normalize_pos)
    squad = to_numeric(squad, ["minutes","age","goals","assists","goals_per_90","assists_per_90","goal_contributions_per_90"])
    if {"player_name","season"}.issubset(squad.columns):
        squad = squad.dropna(subset=["player_name","season"])

# Normalize scouting data
if not scouting.empty:
    aliases = {
        "player_name":["player_name","player","name"], "team":["team","club"],
        "league":["league","competition"], "position_group":["position_group"],
        "minutes":["minutes","playing_time_min"], "age":["age"],
        "scouting_score":["scouting_screen_score","scouting_score"],
    }
    for target, candidates in aliases.items():
        if target not in scouting.columns:
            src = next((c for c in candidates if c in scouting.columns), None)
            if src: scouting[target] = scouting[src]
    if "position_group" not in scouting and "pos" in scouting:
        scouting["position_group"] = scouting["pos"].apply(normalize_pos)
    scouting = to_numeric(scouting, [
        "minutes","age","scouting_score","scouting_screen_score",
        "goals_per_90","assists_per_90","goal_contributions_per_90",
        "shots_per_90","shots_on_target_per_90","tackles_won_per_90",
        "interceptions_per_90","crosses_per_90","priority_score",
    ])
    if "scouting_score" not in scouting and "scouting_screen_score" in scouting:
        scouting["scouting_score"] = scouting["scouting_screen_score"]

if not market_values.empty:
    if "player_name" not in market_values.columns:
        market_values = pd.DataFrame()
    else:
        market_values["market_value_eur"] = pd.to_numeric(market_values.get("market_value_eur"), errors="coerce")

# Sidebar filters
st.sidebar.header("Dashboard controls")
st.sidebar.caption("Фильтры Scouting и Squad Analysis независимы.")
if squad.empty:
    st.error("Не найден dataset Real Madrid из Notebook 02.")
    st.code("data/processed/real_madrid_player_season_laliga_2023_2026.csv")
    st.stop()

seasons = sorted(squad["season"].dropna().unique().tolist()) if "season" in squad else []
selected_seasons = st.sidebar.multiselect("Сезоны Real Madrid", seasons, default=seasons)
pos_values = sorted(squad["position_group"].dropna().unique().tolist()) if "position_group" in squad else []
selected_positions = st.sidebar.multiselect("Позиции состава", pos_values, default=[p for p in pos_values if p != "Unknown"])
min_minutes = st.sidebar.slider("Минимум минут в составе", 0, 3000, 450, 50)

filtered = squad.copy()
if selected_seasons and "season" in filtered: filtered = filtered[filtered["season"].isin(selected_seasons)]
if selected_positions and "position_group" in filtered: filtered = filtered[filtered["position_group"].isin(selected_positions)]
if "minutes" in filtered: filtered = filtered[filtered["minutes"].fillna(0) >= min_minutes]

tabs = st.tabs(["Overview","Squad analysis","Scouting","Player profile","Transfer planning","Data & methodology"])

# OVERVIEW
with tabs[0]:
    st.subheader("Executive overview")
    a,b,c,d = st.columns(4)
    a.metric("Player-season records", f"{len(filtered):,}")
    a2 = filtered["player_name"].nunique() if "player_name" in filtered else len(filtered)
    b.metric("Unique players", f"{a2:,}")
    c.metric("Average age", f"{filtered['age'].mean():.1f}" if "age" in filtered and filtered["age"].notna().any() else "—")
    d.metric("Total minutes", f"{filtered['minutes'].sum():,.0f}" if "minutes" in filtered else "—")
    if not scouting.empty:
        x,y,z = st.columns(3)
        x.metric("Scouting shortlist", f"{len(scouting):,}")
        y.metric("Full scouting pool", f"{len(scouting_pool):,}" if not scouting_pool.empty else "—")
        z.metric("Positions covered", str(scouting["position_group"].nunique()) if "position_group" in scouting else "—")
    if "season" in filtered and "minutes" in filtered:
        g = filtered.groupby("season",as_index=False)["minutes"].sum()
        st.plotly_chart(px.bar(g,x="season",y="minutes",title="Squad minutes by season",template="plotly_dark"),use_container_width=True)
    l,r = st.columns(2)
    with l:
        if {"season","age"}.issubset(filtered.columns):
            st.plotly_chart(px.box(filtered.dropna(subset=["age"]),x="season",y="age",points="all",title="Age distribution",template="plotly_dark"),use_container_width=True)
    with r:
        if "position_group" in filtered:
            p=filtered.groupby("position_group")["player_name"].nunique().reset_index(name="players")
            st.plotly_chart(px.bar(p,x="position_group",y="players",title="Squad players by position",template="plotly_dark"),use_container_width=True)

# SQUAD
with tabs[1]:
    st.subheader("Real Madrid squad analysis")
    if {"season","position_group"}.issubset(filtered.columns):
        metrics=[c for c in ["minutes","goals","assists","goals_per_90","assists_per_90","goal_contributions_per_90"] if c in filtered]
        if metrics:
            m=st.selectbox("Squad metric",metrics)
            agg="mean" if "per_90" in m else "sum"
            g=filtered.groupby(["season","position_group"],as_index=False)[m].agg(agg)
            st.plotly_chart(px.line(g,x="season",y=m,color="position_group",markers=True,title=f"{m.replace('_',' ').title()} by season and position",template="plotly_dark"),use_container_width=True)
    if "minutes" in filtered:
        cols=[c for c in ["season","player_name","position_group","age","minutes","goals","assists","goals_per_90","assists_per_90"] if c in filtered]
        st.dataframe(filtered.sort_values("minutes",ascending=False)[cols],use_container_width=True,hide_index=True)
    if not ratings.empty:
        with st.expander("Notebook 04 — player ratings"):
            st.dataframe(ratings,use_container_width=True,hide_index=True)

# SCOUTING
with tabs[2]:
    st.subheader("External scouting — 2025/26")
    if scouting.empty:
        st.warning("Не найден external_scouting_shortlist_2025_26.csv. Помести файл в data/processed/.")
    else:
        st.caption("60 кандидатов: целевой shortlist до 20 игроков на каждую outfield-позицию. Это статистический скрининг, не список подтверждённых трансферных целей.")
        sc=scouting.copy()
        f1,f2,f3,f4=st.columns(4)
        pos_opts=sorted(sc["position_group"].dropna().unique()) if "position_group" in sc else []
        league_opts=sorted(sc["league"].dropna().unique()) if "league" in sc else []
        with f1: psel=st.multiselect("Position",pos_opts,default=pos_opts,key="sc_pos")
        with f2: lsel=st.multiselect("League",league_opts,default=league_opts,key="sc_league")
        with f3:
            amin=int(np.nanmin(sc["age"])) if "age" in sc and sc["age"].notna().any() else 16
            amax=int(np.nanmax(sc["age"])) if "age" in sc and sc["age"].notna().any() else 40
            age_range=st.slider("Age range",amin,amax,(amin,amax))
        with f4:
            mins_min=int(max(0,sc["minutes"].min())) if "minutes" in sc and sc["minutes"].notna().any() else 0
            mins_max=int(sc["minutes"].max()) if "minutes" in sc and sc["minutes"].notna().any() else 4000
            mins_range=st.slider("Minutes range",mins_min,mins_max,(mins_min,mins_max),step=50)
        if psel and "position_group" in sc: sc=sc[sc["position_group"].isin(psel)]
        if lsel and "league" in sc: sc=sc[sc["league"].isin(lsel)]
        if "age" in sc: sc=sc[sc["age"].between(age_range[0],age_range[1])]
        if "minutes" in sc: sc=sc[sc["minutes"].between(mins_range[0],mins_range[1])]
        score_col="priority_score" if "priority_score" in sc else ("scouting_score" if "scouting_score" in sc else None)
        k1,k2,k3,k4=st.columns(4)
        k1.metric("Filtered candidates",len(sc))
        k2.metric("Average age",f"{sc['age'].mean():.1f}" if "age" in sc and sc["age"].notna().any() else "—")
        k3.metric("Median minutes",f"{sc['minutes'].median():,.0f}" if "minutes" in sc and sc["minutes"].notna().any() else "—")
        k4.metric("Median screening score",f"{sc[score_col].median():.1f}" if score_col and sc[score_col].notna().any() else "—")
        if score_col and not sc.empty:
            top=sc.sort_values(score_col,ascending=False).head(20).sort_values(score_col)
            st.plotly_chart(px.bar(top,x=score_col,y="player_name",color="position_group",orientation="h",title="Top candidates after filters",template="plotly_dark"),use_container_width=True)
        with st.expander("Shortlist by position and league",expanded=True):
            if {"position_group","league"}.issubset(sc.columns):
                counts=sc.groupby(["position_group","league"]).size().reset_index(name="players")
                st.dataframe(counts.pivot(index="position_group",columns="league",values="players").fillna(0).astype(int),use_container_width=True)
        display_cols=[c for c in ["player_name","team","league","position_group","pos","age","minutes","scouting_score","scouting_screen_score","priority_score","goals_per_90","assists_per_90","goal_contributions_per_90","shots_per_90","shots_on_target_per_90","tackles_won_per_90","interceptions_per_90","crosses_per_90"] if c in sc]
        st.dataframe(sc.sort_values(score_col,ascending=False)[display_cols] if score_col else sc[display_cols],use_container_width=True,hide_index=True)
        st.caption("Игроки с 300–449 минутами имеют меньшую выборку. Сравнение между лигами требует осторожности.")

# PLAYER PROFILE
with tabs[3]:
    st.subheader("Player profile & comparison")
    if scouting.empty:
        st.info("Для профиля загрузите shortlist из Notebook 06.")
    else:
        prof=scouting.copy()
        prof["player_label"]=prof["player_name"].astype(str)+" — "+prof.get("team",pd.Series("",index=prof.index)).astype(str)
        labels=prof["player_label"].tolist()
        chosen=st.selectbox("Select player",labels,key="profile_player")
        row=prof.loc[prof["player_label"]==chosen].iloc[0]
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Position",str(row.get("position_group","—")))
        m2.metric("Age",f"{row['age']:.0f}" if pd.notna(row.get("age",np.nan)) else "—")
        m3.metric("Minutes",f"{row['minutes']:,.0f}" if pd.notna(row.get("minutes",np.nan)) else "—")
        scval=row.get("scouting_score",row.get("scouting_screen_score",np.nan))
        m4.metric("Screening score",f"{scval:.1f}" if pd.notna(scval) else "—")
        st.write(f"**Club:** {row.get('team','—')}  |  **League:** {row.get('league','—')}  |  **Season:** {row.get('season','2025-2026')}")
        metrics=["goals_per_90","assists_per_90","shots_per_90","shots_on_target_per_90","tackles_won_per_90","interceptions_per_90","crosses_per_90"]
        available=[c for c in metrics if c in prof.columns and prof[c].notna().any()]
        if available:
            pos_group=row.get("position_group","")
            peers=prof[prof["position_group"]==pos_group] if "position_group" in prof else prof
            pct=[]
            vals=[]
            for c in available:
                v=row.get(c,np.nan)
                vals.append(float(v) if pd.notna(v) else 0)
                pct.append(float((peers[c] <= v).mean()*100) if pd.notna(v) and peers[c].notna().any() else 0)
            radar=pd.DataFrame({"metric":available,"percentile":pct})
            fig=px.line_polar(radar,r="percentile",theta="metric",line_close=True,range_r=[0,100],title="Position-group percentile profile",template="plotly_dark")
            fig.update_traces(fill="toself")
            st.plotly_chart(fig,use_container_width=True)
            st.caption("Percentiles рассчитаны относительно игроков той же позиционной группы внутри shortlist, а не всей лиги.")
        comp=st.multiselect("Compare with other candidates", [x for x in labels if x!=chosen], max_selections=3,key="profile_compare")
        if comp:
            chosen_rows=prof[prof["player_label"].isin([chosen]+comp)]
            cmetrics=[c for c in ["goals_per_90","assists_per_90","goal_contributions_per_90","shots_per_90","tackles_won_per_90","interceptions_per_90","crosses_per_90"] if c in chosen_rows and chosen_rows[c].notna().any()]
            if cmetrics:
                long=chosen_rows.melt(id_vars=["player_label"],value_vars=cmetrics,var_name="metric",value_name="value")
                st.plotly_chart(px.bar(long,x="metric",y="value",color="player_label",barmode="group",title="Candidate comparison",template="plotly_dark"),use_container_width=True)

# TRANSFER PLANNING
with tabs[4]:
    st.subheader("Transfer planning — 2026/27 scenario")
    budget_default=float(summary.get("budget_assumption_eur",200_000_000))
    budget=st.number_input("Scenario budget (€)",min_value=0.0,value=budget_default,step=10_000_000.0,format="%.0f")
    premium=st.slider("Scenario premium over market value (%)",0,100,25,5)
    max_signings=st.slider("Maximum signings",1,5,3)
    if not need.empty and "position_group" in need and "need_score" in need:
        st.plotly_chart(px.bar(need.sort_values("need_score"),x="need_score",y="position_group",orientation="h",title="Squad recruitment-need heuristic",template="plotly_dark"),use_container_width=True)
        st.dataframe(need,use_container_width=True,hide_index=True)
    if scouting.empty:
        st.warning("Shortlist is missing.")
    elif market_values.empty:
        st.warning("Market-value CSV is missing. Scenario optimizer cannot estimate costs without values.")
    else:
        candidates=scouting.merge(market_values,on="player_name",how="left",suffixes=("","_market"))
        if "position_group" not in candidates and "pos" in candidates:
            candidates["position_group"]=candidates["pos"].apply(normalize_pos)
        candidates["scenario_cost_eur"]=candidates["market_value_eur"]*(1+premium/100)
        candidates["scenario_cost_eur"]=pd.to_numeric(candidates["scenario_cost_eur"],errors="coerce")
        candidates["score"]=pd.to_numeric(candidates.get("priority_score",candidates.get("scouting_score")),errors="coerce")
        candidates["score"]=candidates["score"].fillna(0)
        priced=candidates.dropna(subset=["market_value_eur","scenario_cost_eur"]).copy()
        x1,x2,x3=st.columns(3)
        x1.metric("Shortlist candidates",len(candidates))
        x2.metric("Candidates with market values",len(priced))
        x3.metric("Candidates without values",len(candidates)-len(priced))
        if not priced.empty:
            st.markdown("#### Market-value evidence")
            evidence_cols=[c for c in ["player_name","team","position_group","market_value_eur","value_date","value_source","source_url"] if c in priced]
            st.dataframe(priced[evidence_cols],use_container_width=True,hide_index=True)
            # Exhaustive scenario search: one player per position group, budget and max-signings constraints.
            ranked=priced.sort_values("score",ascending=False).head(30)
            best=None
            best_score=-1
            for n in range(1,min(max_signings,len(ranked))+1):
                for combo in combinations(ranked.index.tolist(),n):
                    subset=ranked.loc[list(combo)]
                    if subset["position_group"].duplicated().any(): continue
                    cost=subset["scenario_cost_eur"].sum()
                    if cost<=budget and subset["score"].sum()>best_score:
                        best=subset
                        best_score=subset["score"].sum()
            if best is not None:
                st.markdown("#### Best feasible scenario")
                total_cost=float(best["scenario_cost_eur"].sum())
                q1,q2,q3=st.columns(3)
                q1.metric("Selected players",len(best))
                q2.metric("Scenario cost",fmt_eur(total_cost))
                q3.metric("Remaining budget",fmt_eur(budget-total_cost))
                selected_cols=[c for c in ["player_name","team","league","position_group","age","minutes","score","market_value_eur","scenario_cost_eur","value_date"] if c in best]
                st.dataframe(best[selected_cols].rename(columns={"score":"screening priority"}),use_container_width=True,hide_index=True)
            else:
                st.info("При текущем бюджете и ограничении не более одного игрока на позиционную группу допустимого набора нет.")
        else:
            st.info("Нет кандидатов с заполненной рыночной стоимостью. Добавьте проверенные оценки в data/external/market_values_2026_11.csv.")
    st.warning("Market value ≠ transfer fee. Надбавка — сценарное допущение, а не прогноз цены сделки. €200m — учебный бюджетный сценарий, не подтверждённый бюджет Real Madrid.")

# DATA
with tabs[5]:
    st.subheader("Data sources, quality & methodology")
    source_rows=[
        ("Real Madrid player-season dataset",squad_path),
        ("External scouting full pool",pool_path),
        ("External scouting shortlist",scouting_path),
        ("Feature coverage audit",REPORTS/"external_scouting_feature_coverage.csv" if (REPORTS/"external_scouting_feature_coverage.csv").exists() else None),
        ("Merge audit",REPORTS/"external_scouting_merge_audit.csv" if (REPORTS/"external_scouting_merge_audit.csv").exists() else None),
        ("Scouting manifest",manifest_path),
        ("Market values",market_path),
        ("Position priorities",need_path),
        ("Player ratings",ratings_path),
    ]
    st.dataframe(pd.DataFrame([{"Dataset":n,"Status":"Loaded" if p and Path(p).exists() else "Not found","Path":str(p) if p else "—"} for n,p in source_rows]),use_container_width=True,hide_index=True)
    if manifest:
        st.markdown("#### Scouting extraction summary")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Full raw pool",f"{manifest.get('rows_full_pool',0):,}")
        c2.metric("Eligible outfield pool",f"{manifest.get('rows_eligible_outfield_pool',0):,}")
        c3.metric("Shortlist rows",f"{manifest.get('rows_shortlist',0):,}")
        c4.metric("Minimum minutes",str(manifest.get("minimum_minutes","—")))
        st.write("**Source:**",manifest.get("source","—"),"| **Season:**",manifest.get("season","—"),"| **Retrieved UTC:**",manifest.get("retrieved_at_utc","—"))
        st.write("**Leagues returned:**",", ".join(manifest.get("leagues_returned",[])))
        st.write("**Features:**",", ".join(manifest.get("features_used",[])))
        st.markdown("#### Recorded limitations")
        for item in manifest.get("limitations",[]): st.markdown(f"- {item}")
    if not market_values.empty:
        st.markdown("#### Market-value data coverage")
        st.write(f"Market-value entries: {market_values['market_value_eur'].notna().sum()} of {len(market_values)} shortlist rows.")
        st.caption("Values are point-in-time estimates. Check value_date and source_url before using them in a scenario.")
    st.markdown("#### Methodology")
    st.markdown("""
    - **Scouting screen:** position-aware percentile screen based on eight per-90 indicators.
    - **Candidate pool:** 2025/26 historical player-season statistics from five FBref-supported leagues; at least 300 minutes for the eligible outfield pool.
    - **Shortlist:** up to 20 players in each broad outfield position group.
    - **Player profile percentiles:** calculated against the 60-player shortlist within the same broad position group.
    - **Scenario cost:** market value × (1 + user-selected premium); this is not a confirmed transfer fee.
    - **Missing values:** treated as unknown and excluded from the budget optimizer, never as zero.
    """)
    st.markdown("#### Data quality")
    audit_path=REPORTS/"external_scouting_merge_audit.csv"
    coverage_path=REPORTS/"external_scouting_feature_coverage.csv"
    if audit_path.exists():
        st.write("Merge audit")
        st.dataframe(pd.read_csv(audit_path),use_container_width=True,hide_index=True)
    if coverage_path.exists():
        st.write("Feature coverage")
        st.dataframe(pd.read_csv(coverage_path),use_container_width=True,hide_index=True)

st.divider()
st.markdown('<p class="small-note">Local analytical dashboard · FBref via SoccerData · Planning season 2026/27 · Historical scouting baseline 2025/26</p>',unsafe_allow_html=True)

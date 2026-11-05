# Real Madrid AI Football Intelligence

An individual academic project that applies football data analytics and machine-learning techniques to support squad assessment, player scouting, and transfer-planning decisions for Real Madrid.

> **Planning scenario:** 2026/27  
> **Historical squad baseline:** La Liga 2023/24–2025/26  
> **External scouting baseline:** 2025/26  
> **Illustrative transfer-planning budget:** €200 million (an academic scenario assumption, not a statement of Real Madrid's actual transfer budget).

## Project overview

The project follows an analytics workflow from data collection to a decision-support dashboard:

1. Collect player-season statistics from FBref using SoccerData.
2. Clean and validate the data; inspect missing values, duplicates, ranges, and merge coverage.
3. Explore Real Madrid's squad composition, age profile, playing time, and performance.
4. Build position-aware player ratings and player archetypes.
5. Compare external players using position-aware scouting indicators.
6. Estimate squad recruitment needs and explore budget-constrained transfer scenarios.
7. Present the results in an interactive Streamlit dashboard.

The system is intended as a **decision-support prototype**. It does not claim to predict transfer success or replace scouting, medical, contractual, financial, or tactical due diligence.

## Dashboard

The Streamlit dashboard contains the following sections:

| Section | Purpose |
|---|---|
| Overview | High-level squad and scouting KPIs |
| Squad Analysis | Season trends, position groups, minutes, age, and player tables |
| Scouting | External shortlist with filters for position, league, age, and minutes |
| Player Profile | Position-group percentile profile and player-to-player comparison |
| Transfer Planning | Budget scenario, market-value assumptions, and candidate-combination search |
| Data & Methodology | Source coverage, merge audit, extraction manifest, and limitations |

### Dashboard preview

Run the app locally to explore the interactive dashboard.

## Data

### Real Madrid squad data

The historical squad dataset is produced by the project's data collection and cleaning notebooks. It covers La Liga player-season records for:

- 2023/24
- 2024/25
- 2025/26

Expected cleaned file:

```text
data/processed/real_madrid_player_season_laliga_2023_2026.csv
```

### External scouting data

The current external scouting extraction uses FBref via SoccerData for five supported competitions:

- English Premier League
- Spanish La Liga
- German Bundesliga
- Italian Serie A
- French Ligue 1

The extraction manifest records:

- 2,839 player-season rows in the full pool
- 1,999 eligible outfield-player rows after the 300-minute filter
- 60 shortlist rows, targeting up to 20 players per broad outfield position group (DF, MF, FW)

Files:

```text
data/processed/external_scouting_pool_2025_26.csv
data/processed/external_scouting_shortlist_2025_26.csv
reports/external_scouting_manifest.json
reports/external_scouting_feature_coverage.csv
reports/external_scouting_merge_audit.csv
```

The shortlist uses these per-90 indicators where available:

- Goals
- Assists
- Goal contributions
- Shots
- Shots on target
- Tackles won
- Interceptions
- Crosses

### Market values and transfer assumptions

Market values are stored separately from player performance data:

```text
data/external/market_values_2026_11.csv
```

A market value is **not** a confirmed transfer fee. The transfer-planning page applies a user-adjustable scenario premium to a sourced market-value estimate. Missing market values remain unknown and are excluded from the budget optimizer; they are never treated as zero.

The €200m budget is an illustrative academic assumption. It is not represented as Real Madrid's actual available budget.

## Repository structure

```text
real-madrid-ai/
├── app.py
├── requirements_dashboard.txt
├── README.md
├── .gitignore
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_data_cleaning_quality.ipynb
│   ├── 03_exploratory_data_analysis.ipynb
│   ├── 04_position_aware_ratings.ipynb
│   ├── 05_player_archetypes_similarity.ipynb
│   ├── 06_external_scouting.ipynb
│   └── 07_transfer_need_budget_optimizer.ipynb
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
└── reports/
```

The notebook filenames above describe the intended workflow; use the actual filenames in your local project if they differ.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPOSITORY>.git
cd <YOUR-REPOSITORY>
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dashboard dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements_dashboard.txt
```

The notebooks may require additional packages, including `soccerdata`, `pyarrow`, `scikit-learn`, `matplotlib`, and `seaborn`. Install the packages listed in the relevant notebook setup cells or maintain a separate full-project requirements file.

### 4. Run the dashboard

From the repository root:

```powershell
python -m streamlit run app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

## Reproducing the analysis

Run the notebooks in order:

1. Data collection
2. Data cleaning and quality checks
3. Exploratory data analysis
4. Position-aware player ratings
5. Player archetypes and similarity
6. External scouting pool and shortlist
7. Transfer need and budget scenario

The dashboard reads the generated CSV and JSON files from `data/processed`, `data/external`, and `reports`. Run the relevant notebooks first if these files are not present.

## Methodology

### Position-aware scouting

Players are evaluated within broad position groups rather than compared indiscriminately across all positions. Per-90 statistics help account for differences in playing time, but do not eliminate sample-size or role-related bias.

### Recruitment-need heuristic

Squad need is estimated from indicators such as the number of players with meaningful minutes and the concentration of minutes among the most-used players. This is a descriptive depth heuristic, not a tactical diagnosis.

### Transfer scenario optimizer

The dashboard explores combinations of candidates under:
- a user-defined illustrative budget;
- a maximum number of signings;
- at most one selected player per broad position group;
- available market-value estimates plus a scenario premium.

The optimizer maximizes the sum of candidate priority scores among feasible combinations. It is a transparent prototype, not a full club transfer model.

## Limitations and responsible interpretation

1. **Historical data:** 2025/26 statistics do not establish a player's current form in 2026/27.
2. **Small samples:** Players with 300–449 minutes have less reliable performance estimates.
3. **Position labels:** Broad FBref position groups approximate roles and may hide tactical differences.
4. **League context:** Competition strength, team style, and tactical roles differ between leagues.
5. **No transfer availability data:** The scouting dataset does not establish contract status, willingness to move, wages, agent fees, medical status, or actual availability.
6. **Market value versus fee:** Public market-value estimates are not negotiated transfer prices; values must be checked against their source dates.
7. **Scoring interpretation:** A screening score is descriptive. It is not a probability of success, future performance, or transfer completion.
8. **Data coverage:** Missing or unmerged metrics can affect candidate comparisons; consult the coverage and merge-audit reports.

## Data sources and attribution

- [FBref](https://fbref.com/) — football player and team statistics.
- [SoccerData](https://github.com/probberechts/soccerdata) — Python package used to retrieve football data from supported sources.
- Market-value sources are recorded per player in the market-value CSV. Check the source URL and value date before citing or using a value.

Respect the terms of use and rate limits of all data providers. This repository is an academic, non-commercial analytical project.

## Academic use and AI disclosure

This project uses Python-based data processing, statistical analysis, machine-learning methods, and a Streamlit dashboard. Any AI-assisted drafting or coding should be disclosed in the final academic submission according to the course or university's rules. Interpretations and final decisions remain the responsibility of the project author.

## License

No license has been selected yet. Until a license is added, do not assume that the repository's code or bundled data may be reused, redistributed, or modified under an open-source license. Also review the redistribution terms of the underlying data sources before publishing raw datasets.

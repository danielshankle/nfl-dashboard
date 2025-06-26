
try:
    import streamlit as st
except ModuleNotFoundError:
    raise ImportError("Streamlit is not installed. Please run `pip install streamlit` before running this app.")

import pandas as pd
import matplotlib.pyplot as plt

# Load data
stats_df = pd.read_csv("nfl_2024_boxscores.csv")
injuries_df = pd.read_csv("nfl_2024_injuries.csv")
snap_df = pd.read_csv("nfl_2024_snap_counts_per_game.csv")

# Preprocess
stats_df['GameLabel'] = stats_df['Date'] + ' — ' + stats_df['Team'] + ' vs ' + stats_df['Opponent'] + ' (' + stats_df['FinalScore'] + ')'
game_options = stats_df[['GameID', 'GameLabel']].drop_duplicates()

# Sidebar filters
st.sidebar.title("NFL Game Selector")
selected_games = st.sidebar.multiselect("Select Games", options=game_options['GameLabel'])
if not selected_games:
    st.info("Please select one or more games.")
    st.stop()

selected_game_ids = game_options[game_options['GameLabel'].isin(selected_games)]['GameID'].tolist()
filtered_stats = stats_df[stats_df['GameID'].isin(selected_game_ids)]
filtered_injuries = injuries_df[injuries_df['GameID'].isin(selected_game_ids)]

teams = filtered_stats['Team'].unique()
selected_team = st.sidebar.selectbox("Select Team", teams)
stat_types = filtered_stats['Stat'].unique()
selected_stat = st.sidebar.selectbox("Select Stat Type", stat_types)

team_data = filtered_stats[(filtered_stats['Team'] == selected_team) & (filtered_stats['Stat'] == selected_stat)]

# Position filter for snap counts
positions = snap_df['Pos'].dropna().unique() if 'Pos' in snap_df.columns else []
selected_position = st.sidebar.selectbox("Select Position (Snap Count)", options=['All'] + sorted(positions.tolist()))

filtered_snaps = snap_df[(snap_df['Team'] == selected_team) & (snap_df['Week'].between(1, 18))]
if selected_position != 'All':
    filtered_snaps = filtered_snaps[filtered_snaps['Pos'] == selected_position]

# Player selection
player_options = sorted(set(team_data['PLAYER'].dropna().unique()) | set(filtered_snaps['Player'].dropna().unique()))
selected_player = st.selectbox("🔍 Deep Dive: Select a Player", player_options)

# Display team stats
st.header(f"{selected_team} — {selected_stat} Across {len(selected_game_ids)} Game(s)")
grouped = team_data.groupby('PLAYER').agg({'YDS': 'sum'}).reset_index() if 'YDS' in team_data.columns else team_data
st.dataframe(grouped)

if 'YDS' in grouped.columns:
    grouped = grouped.sort_values('YDS', ascending=False)
    fig, ax = plt.subplots()
    grouped.set_index('PLAYER')['YDS'].plot(kind='barh', ax=ax)
    ax.set_xlabel('Total Yards')
    ax.set_title(f'{selected_team} {selected_stat} (Combined Yards)')
    st.pyplot(fig)

# Snap counts
st.subheader(f"{selected_team} — Snap Counts")
if not filtered_snaps.empty:
    st.dataframe(filtered_snaps[['Week', 'Player', 'Pos', 'Offense', 'Defense', 'ST']])
    filtered_snaps['TotalSnaps'] = filtered_snaps[['Offense', 'Defense', 'ST']].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
    total_snaps = filtered_snaps.groupby('Player')['TotalSnaps'].sum().sort_values(ascending=False).reset_index()
    st.bar_chart(total_snaps.set_index('Player'))
else:
    st.info("No snap count data available for that team/position.")

# Injuries
st.subheader(f"{selected_team} — Injuries in Selected Games")
inj = filtered_injuries[filtered_injuries['Team'] == selected_team]
if not inj.empty:
    st.dataframe(inj[['PlayerInjury', 'Date']])
else:
    st.write("No injuries reported.")

# Side-by-side comparison
st.header(f"🔍 {selected_team} — Side-by-Side Overview")
cols = st.columns(3)

with cols[0]:
    st.subheader("Player Stats")
    display_stats = team_data[['PLAYER', 'Stat', 'YDS']] if 'YDS' in team_data.columns else team_data
    st.dataframe(display_stats)

with cols[1]:
    st.subheader("Snap Counts")
    if not filtered_snaps.empty:
        st.dataframe(filtered_snaps[['Player', 'Pos', 'Offense', 'Defense', 'ST']])
    else:
        st.write("No snap count data.")

with cols[2]:
    st.subheader("Injuries")
    if not inj.empty:
        st.dataframe(inj[['PlayerInjury', 'Date']])
    else:
        st.write("No injuries.")

# Deep dive for selected player
st.header(f"📌 Deep Dive: {selected_player}")

# Game-by-game stats
st.subheader("Game-by-Game Stats")
player_stats = stats_df[(stats_df['PLAYER'] == selected_player) &
                        (stats_df['Team'] == selected_team) &
                        (stats_df['GameID'].isin(selected_game_ids))]

if not player_stats.empty:
    st.dataframe(player_stats[['Date', 'Stat', 'YDS', 'Opponent', 'FinalScore']])
    if 'YDS' in player_stats.columns:
        fig, ax = plt.subplots()
        grouped = player_stats.groupby('Date')['YDS'].sum().sort_index()
        grouped.plot(kind='bar', ax=ax)
        ax.set_title(f'{selected_player} — Total Yards per Game')
        st.pyplot(fig)
else:
    st.write("No stat records found.")

# Game-by-game snap counts
st.subheader("Game-by-Game Snap Counts")
player_snaps = filtered_snaps[filtered_snaps['Player'] == selected_player]
if not player_snaps.empty:
    st.dataframe(player_snaps[['Week', 'Pos', 'Offense', 'Defense', 'ST']])
    try:
        snap_plot_data = player_snaps[['Week', 'Offense', 'Defense', 'ST']].copy()
        snap_plot_data = snap_plot_data.set_index('Week').apply(pd.to_numeric, errors='coerce')
        st.line_chart(snap_plot_data)
    except:
        st.write("Snap chart could not be rendered.")
else:
    st.write("No snap count data for player.")

# Injury history
st.subheader("Injury Report")
player_injuries = injuries_df[(injuries_df['Team'] == selected_team) &
                              (injuries_df['PlayerInjury'].str.contains(selected_player, case=False, na=False)) &
                              (injuries_df['GameID'].isin(selected_game_ids))]
if not player_injuries.empty:
    st.dataframe(player_injuries[['PlayerInjury', 'Date']])
else:
    st.write("No injury record found.")

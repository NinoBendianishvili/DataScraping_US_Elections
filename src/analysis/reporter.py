"""
Handles data analysis and generation of HTML reports with visualizations.
This module consolidates the logic from the original analyzer.py and generator.py.
"""
import os
import logging
import pandas as pd
import plotly.express as px
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import List, Dict, Optional, Any
import sqlite3
from src.data.database import DB_PATH


logger = logging.getLogger(__name__)
PARTY_COLORS = {'Democratic': 'blue', 'Republican': 'red'}
YEAR_COL, STATE_NAME_COL, WINNER_COL = 'year', 'state_name', 'state_winner'
DEM_LEADER_COL, REP_LEADER_COL = 'dem_leader', 'rep_leader'
DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL = 'dem_national_votes', 'rep_national_votes'
TOTAL_NAT_VOTE_COL = 'total_national_votes' # Added for clarity
DEM_STATE_PCT_COL, REP_STATE_PCT_COL = 'dem_state_percentage', 'rep_state_percentage'

def _load_and_clean_data() -> Optional[pd.DataFrame]:
    """Loads and cleans the election data by querying the SQLite database."""
    logger.info(f"Loading data from database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}. Please run the scraper first.")
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT
                r.year, r.state_name, s.electoral_votes, r.state_winner,
                r.dem_state_percentage, r.rep_state_percentage,
                e.dem_leader, e.rep_leader,
                e.dem_national_votes, e.rep_national_votes, e.total_national_votes
            FROM results r
            LEFT JOIN states s ON r.state_name = s.state_name
            LEFT JOIN elections e ON r.year = e.year
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # --- THIS IS THE CRITICAL FIX ---
        # Define the columns that should be numeric.
        vote_cols = [DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL, TOTAL_NAT_VOTE_COL]
        # Convert vote columns to numeric, coercing errors to NaN (Not a Number).
        # This handles any missing values gracefully.
        for col in vote_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        logger.info(f"Successfully loaded data from database. Shape: {df.shape}")
        # Drop rows where essential data for analysis is missing.
        df.dropna(subset=[YEAR_COL, STATE_NAME_COL, WINNER_COL], inplace=True)
        df[YEAR_COL] = df[YEAR_COL].astype(int)

        return df
    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        logger.error(f"Failed to load data from database: {e}", exc_info=True)
        return None

def _create_national_trends_plot(df: pd.DataFrame) -> Optional[str]:
    """Generates a Plotly bar chart for national vote trends."""
    logger.info("Generating national trends bar chart...")
    try:
        # Group by year and take the first entry for national votes
        national_df = df.groupby(YEAR_COL)[[DEM_NAT_VOTE_COL, REP_NAT_VOTE_COL]].first().reset_index()

        # --- FIX: Ensure the 'total' column is a sum of numbers, not strings ---
        # This will now work because the columns are numeric.
        national_df['total'] = national_df[DEM_NAT_VOTE_COL] + national_df[REP_NAT_VOTE_COL]

        # Calculate percentages
        national_df['Democratic (%)'] = (national_df[DEM_NAT_VOTE_COL] / national_df['total']) * 100
        national_df['Republican (%)'] = (national_df[REP_NAT_VOTE_COL] / national_df['total']) * 100

        plot_df = national_df.melt(id_vars=YEAR_COL, value_vars=['Democratic (%)', 'Republican (%)'],
                                   var_name='Party', value_name='Percentage')

        fig = px.bar(plot_df, x=YEAR_COL, y='Percentage', color='Party', barmode='group',
                     title="National Popular Vote Share (%) by Year",
                     labels={'Percentage': 'Vote Percentage (%)', YEAR_COL: 'Election Year'},
                     text_auto='.1f', color_discrete_map=PARTY_COLORS)
        fig.update_layout(yaxis_range=[0, 100], legend_title_text='Party')
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        logger.error(f"Failed to create national bar chart: {e}", exc_info=True)
        return None

def _create_state_trends_plot(df: pd.DataFrame, state_name: str) -> Optional[str]:
    """Generates a Plotly bar chart for a single state's vote trends."""
    state_df = df[df[STATE_NAME_COL] == state_name]
    if state_df.empty: return None

    plot_df = state_df.melt(id_vars=YEAR_COL, value_vars=[DEM_STATE_PCT_COL, REP_STATE_PCT_COL],
                            var_name='Party', value_name='Percentage')
    plot_df['Party'] = plot_df['Party'].map({DEM_STATE_PCT_COL: 'Democratic', REP_STATE_PCT_COL: 'Republican'})

    fig = px.bar(plot_df, x=YEAR_COL, y='Percentage', color='Party', barmode='group',
                 title=f"{state_name} Presidential Vote Share (%)", text_auto='.1f',
                 color_discrete_map=PARTY_COLORS, labels={'Percentage': 'State Vote %'})
    fig.update_layout(yaxis_range=[0, 100], showlegend=False)
    return fig.to_html(full_html=False, include_plotlyjs=False)

def _create_election_map_plot(df_year: pd.DataFrame, year: int, include_js: bool) -> Optional[str]:
    """Creates a Plotly choropleth map for a single election year."""
    try:
        fig = px.choropleth(
            df_year, locations=STATE_NAME_COL, locationmode='USA-states',
            color=WINNER_COL, hover_name=STATE_NAME_COL,
            hover_data={DEM_LEADER_COL: True, REP_LEADER_COL: True},
            color_discrete_map=PARTY_COLORS, scope='usa',
            title=f"U.S. Presidential Election Results - {year}"
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='Winning Party')
        return fig.to_html(full_html=False, include_plotlyjs=include_js)
    except Exception as e:
        logger.error(f"Failed to create map for year {year}: {e}", exc_info=True)
        return None

def _render_and_save_report(template_dir: str, template_name: str, context: Dict[str, Any], output_path: str):
    """Renders a Jinja2 template and saves it to a file."""
    try:
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(['html']))
        template = env.get_template(template_name)
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Successfully generated report: {output_path}")
    except Exception as e:
        logger.error(f"Failed to render or save report {template_name}: {e}", exc_info=True)

def generate_analysis_reports(report_dir: str, bar_chart_filename: str,
                              static_maps_filename: str, template_config: Dict[str, str], **kwargs):
    """Main function to generate all analysis reports."""
    # The function no longer needs input_csv_path
    df = _load_and_clean_data()
    if df is None or df.empty:
        logger.error("Analysis aborted due to data loading failure.")
        return

    # --- 1. Generate Bar Chart Report ---
    national_plot_div = _create_national_trends_plot(df)
    state_plot_divs = {
        state: _create_state_trends_plot(df, state)
        for state in sorted(df[STATE_NAME_COL].unique())
    }
    bar_chart_context = {
        'national_plot_div': national_plot_div,
        'state_plot_divs': {k: v for k, v in state_plot_divs.items() if v}
    }
    _render_and_save_report(
        template_dir=os.path.join(os.path.dirname(__file__), template_config['template_dir']),
        template_name=template_config['bar_chart_template'],
        context=bar_chart_context,
        output_path=os.path.join(report_dir, bar_chart_filename)
    )

    # --- 2. Generate Static Maps Report ---
    map_divs = {}
    years = sorted(df[YEAR_COL].unique())
    for i, year in enumerate(years):
        df_year = df[df[YEAR_COL] == year]
        # Include Plotly.js only for the first map
        map_div = _create_election_map_plot(df_year, year, include_js=(i == 0))
        if map_div:
            map_divs[year] = map_div

    maps_context = {
        'map_divs': map_divs,
        'years_sorted': sorted(map_divs.keys())
    }
    _render_and_save_report(
        template_dir=os.path.join(os.path.dirname(__file__), template_config['template_dir']),
        template_name=template_config['map_report_template'],
        context=maps_context,
        output_path=os.path.join(report_dir, static_maps_filename)
    )
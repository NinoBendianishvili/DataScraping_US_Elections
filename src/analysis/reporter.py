"""
Complete election reporter with both maps and trends reports using database
"""
import json
import logging
import pandas as pd
import sqlite3
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from src.data.database import DB_PATH

logger = logging.getLogger(__name__)

# State abbreviation mapping
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

def _get_db_connection():
    """Helper to get database connection"""
    return sqlite3.connect(DB_PATH)

def _load_election_data() -> Dict[int, Dict[str, List[str]]]:
    """Load election data for maps from database"""
    election_by_year = defaultdict(lambda: {"dem": [], "rep": []})

    try:
        conn = _get_db_connection()
        query = """
            SELECT r.year, r.state_name, r.state_winner
            FROM results r
            WHERE r.state_name IN ({})
            ORDER BY r.year
        """.format(",".join([f"'{state}'" for state in STATE_ABBR.keys()]))

        for row in conn.execute(query):
            year, state, winner = row
            abbr = STATE_ABBR.get(state)
            if not abbr:
                continue

            if "democrat" in winner.lower():
                election_by_year[year]["dem"].append(abbr)
            elif "republican" in winner.lower():
                election_by_year[year]["rep"].append(abbr)

        return dict(election_by_year)
    except Exception as e:
        logger.error(f"Database error loading election data: {e}")
        return {}
    finally:
        conn.close()

def _load_trends_data() -> Tuple[pd.DataFrame, List[int]]:
    """Load data for trends report"""
    try:
        conn = _get_db_connection()
        query = """
            SELECT 
                r.year, 
                r.state_name,
                r.dem_state_percentage,
                r.rep_state_percentage,
                e.dem_national_votes,
                e.rep_national_votes
            FROM results r
            JOIN elections e ON r.year = e.year
            ORDER BY r.year, r.state_name
        """
        df = pd.read_sql_query(query, conn)

        # Clean data
        numeric_cols = ['dem_state_percentage', 'rep_state_percentage',
                        'dem_national_votes', 'rep_national_votes']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        years = sorted(df['year'].unique())
        return df, years
    except Exception as e:
        logger.error(f"Database error loading trends data: {e}")
        return pd.DataFrame(), []
    finally:
        conn.close()

def _generate_map_html(election_data: dict) -> str:
    """Generate HTML for the interactive maps report"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Election Maps</title>
        <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
        <style>
            body {{ font-family: Arial; background: #f8f9fa; padding: 20px; }}
            .container {{ 
                max-width: 1000px; margin: 0 auto; 
                background: white; padding: 20px; border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .map-container {{ display: none; }}
            .map-container.active {{ display: block; }}
            select {{ 
                display: block; margin: 20px auto; padding: 8px; 
                font-size: 16px; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>U.S. Election Results</h1>
            <select id="year-selector">
                {''.join(f'<option value="{year}">{year}</option>' for year in sorted(election_data))}
            </select>
            
            {''.join(
        f'<div id="map-{year}" class="map-container">'
        f'<h2>{year} Results</h2><div id="plot-{year}"></div></div>'
        for year in sorted(election_data)
    )}
        </div>

        <script>
            const data = {json.dumps(election_data)};
            
            function plotMap(year) {{
                const states = data[year];
                Plotly.newPlot(`plot-${{year}}`, [
                    {{
                        type: 'choropleth',
                        locations: states.dem,
                        z: Array(states.dem.length).fill(0),
                        locationmode: 'USA-states',
                        colorscale: [[0, 'blue'], [1, 'blue']],
                        showscale: false,
                        name: 'Democrat'
                    }},
                    {{
                        type: 'choropleth',
                        locations: states.rep,
                        z: Array(states.rep.length).fill(1),
                        locationmode: 'USA-states',
                        colorscale: [[0, 'red'], [1, 'red']],
                        showscale: false,
                        name: 'Republican'
                    }}
                ], {{
                    geo: {{ scope: 'usa', projection: {{ type: 'albers usa' }} }},
                    margin: {{ t: 50, l: 0, r: 0, b: 0 }}
                }});
            }}

            document.getElementById('year-selector').addEventListener('change', function() {{
                document.querySelectorAll('.map-container').forEach(el => 
                    el.classList.remove('active'));
                const year = this.value;
                const mapEl = document.getElementById(`map-${{year}}`);
                mapEl.classList.add('active');
                plotMap(year);
            }});

            // Load first year
            const firstYear = Object.keys(data)[0];
            document.getElementById(`map-${{firstYear}}`).classList.add('active');
            plotMap(firstYear);
        </script>
    </body>
    </html>
    """

def _generate_trends_html(df: pd.DataFrame, years: list) -> str:
    """Generate HTML for the trends report"""
    # National trends
    national = df.groupby('year')[['dem_national_votes', 'rep_national_votes']].sum()
    national['dem_pct'] = (national['dem_national_votes'] /
                           (national['dem_national_votes'] + national['rep_national_votes'])) * 100
    national['rep_pct'] = 100 - national['dem_pct']

    # State trends (example for a few states)
    states = ['California', 'Texas', 'Florida', 'New York', 'Ohio']
    state_data = {state: df[df['state_name'] == state] for state in states}

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Election Trends</title>
        <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
        <style>
            body {{ font-family: Arial; background: #f8f9fa; padding: 20px; }}
            .container {{ 
                max-width: 1200px; margin: 0 auto; 
                background: white; padding: 20px; border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .plot {{ margin: 30px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Election Trends {min(years)}-{max(years)}</h1>
            
            <div class="plot">
                <h2>National Vote Share</h2>
                <div id="national-plot"></div>
            </div>
            
            {''.join(
        f'<div class="plot"><h2>{state} Trends</h2><div id="state-{state.lower()}"></div></div>'
        for state in states
    )}
        </div>

        <script>
            // National plot
            Plotly.newPlot('national-plot', [
                {{
                    x: {json.dumps(national.index.tolist())},
                    y: {json.dumps(national['dem_pct'].tolist())},
                    name: 'Democrat',
                    type: 'bar',
                    marker: {{ color: 'blue' }}
                }},
                {{
                    x: {json.dumps(national.index.tolist())},
                    y: {json.dumps(national['rep_pct'].tolist())},
                    name: 'Republican', 
                    type: 'bar',
                    marker: {{ color: 'red' }}
                }}
            ], {{
                barmode: 'stack',
                yaxis: {{ title: 'Vote Percentage' }}
            }});

            // State plots
            {''.join(
        f"Plotly.newPlot('state-{state.lower()}', ["
        f"{{"
        f"x: {json.dumps(state_data[state]['year'].tolist())}, "
        f"y: {json.dumps(state_data[state]['dem_state_percentage'].tolist())}, "
        f"name: 'Democrat', type: 'line', line: {{ color: 'blue' }} "
        f"}}, "
        f"{{"
        f"x: {json.dumps(state_data[state]['year'].tolist())}, "
        f"y: {json.dumps(state_data[state]['rep_state_percentage'].tolist())}, "
        f"name: 'Republican', type: 'line', line: {{ color: 'red' }} "
        f"}}"
        f"], {{ yaxis: {{ title: 'Vote Percentage', range: [0, 100] }} }});"
        for state in states
    )}
        </script>
    </body>
    </html>
    """

def generate_maps_report(output_path: str):
    """Generate interactive maps report"""
    election_data = _load_election_data()
    if not election_data:
        logger.error("No election data available for maps")
        return

    html = _generate_map_html(election_data)
    with open(output_path, 'w') as f:
        f.write(html)
    logger.info(f"Maps report generated at {output_path}")

def generate_trends_report(output_path: str):
    """Generate trends analysis report"""
    df, years = _load_trends_data()
    if df.empty:
        logger.error("No trends data available")
        return

    html = _generate_trends_html(df, years)
    with open(output_path, 'w') as f:
        f.write(html)
    logger.info(f"Trends report generated at {output_path}")
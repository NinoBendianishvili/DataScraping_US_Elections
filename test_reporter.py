import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.analysis.reporter import _load_and_clean_data, _create_national_trends_plot, generate_analysis_reports

@pytest.fixture
def sample_dataframe():
    """Provides a sample DataFrame as if it were loaded from the database."""
    data = {
        'year': [2020, 2020, 2016, 2016],
        'state_name': ['StateA', 'StateB', 'StateA', 'StateB'],
        'electoral_votes': [10, 5, 10, 5],
        'state_winner': ['DEMOCRAT', 'REPUBLICAN', 'REPUBLICAN', 'DEMOCRAT'],
        'dem_state_percentage': [55.0, 45.0, 48.0, 51.0],
        'rep_state_percentage': [45.0, 55.0, 52.0, 49.0],
        'dem_leader': ['Biden', 'Biden', 'Clinton', 'Clinton'],
        'rep_leader': ['Trump', 'Trump', 'Trump', 'Trump'],
        'dem_national_votes': [81, 81, 65, 65],
        'rep_national_votes': [74, 74, 63, 63],
        'total_national_votes': [155, 155, 128, 128]
    }
    return pd.DataFrame(data)

@patch('src.analysis.reporter.os.path.exists', return_value=True)
@patch('sqlite3.connect')
@patch('pandas.read_sql_query')
def test_load_and_clean_data_success(mock_read_sql, mock_connect, mock_exists, sample_dataframe):
    """Tests successful data loading and cleaning."""
    mock_read_sql.return_value = sample_dataframe.copy()
    
    df = _load_and_clean_data()

    mock_exists.assert_called_once()
    mock_connect.assert_called_once()
    mock_read_sql.assert_called_once()
    
    assert not df.empty
    assert df.shape[0] == 4
    # Test cleaning step: winner column should be standardized
    assert 'Democratic' in df['state_winner'].unique()
    assert 'Republican' in df['state_winner'].unique()
    # Test that year is int
    assert df['year'].dtype == 'int64'

@patch('src.analysis.reporter.os.path.exists', return_value=False)
def test_load_data_db_not_found(mock_exists, caplog):
    """Tests response when the database file is not found."""
    result = _load_and_clean_data()
    assert result is None
    assert "Database file not found" in caplog.text

def test_create_national_trends_plot(sample_dataframe):
    """Tests that the plotting function returns an HTML string."""
    # We don't need to mock plotly here, as it can run on the sample DF.
    # The goal is to confirm it runs and produces output.
    html_div = _create_national_trends_plot(sample_dataframe)
    assert isinstance(html_div, str)
    assert 'class="plotly-graph-div"' in html_div
    assert 'National Popular Vote Share' in html_div


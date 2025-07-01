import pytest
from unittest.mock import patch, mock_open, MagicMock

# Import models to create test data
from src.data.models import ElectionResult, StateData, YearData, Party
# Import functions to be tested
from src.data.processors import save_to_csv, save_to_json, _convert_result_to_dict

@pytest.fixture
def sample_election_results():
    """Provides a list of ElectionResult objects for testing."""
    state1 = StateData("Testland", 10)
    state2 = StateData("Pythania", 5)
    year2020 = YearData(2020, "Joe Test", "Don Test", "1,000,000", "800,000")
    
    return [
        ElectionResult(state1, year2020, 55.0, 45.0, Party.DEMOCRATIC),
        ElectionResult(state2, year2020, 40.0, 60.0, Party.REPUBLICAN)
    ]

def test_convert_result_to_dict(sample_election_results):
    """Tests the helper function that converts an ElectionResult to a dict."""
    result = sample_election_results[0]
    result_dict = _convert_result_to_dict(result)

    assert result_dict['year'] == 2020
    assert result_dict['state'] == "Testland"
    assert result_dict['state_results']['winner'] == "Democratic"
    assert result_dict['national_popular_vote']['total'] == 1800000

@patch('src.data.processors.os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_save_to_csv_success(mock_file, mock_makedirs, sample_election_results):
    """Tests that save_to_csv writes the correct header and rows."""
    filepath = "fake/path/data.csv"
    
    # Mock the CSV writer to inspect what's being written
    mock_writer = MagicMock()
    with patch('csv.DictWriter', return_value=mock_writer):
        save_to_csv(sample_election_results, filepath)

    mock_makedirs.assert_called_once_with("fake/path", exist_ok=True)
    mock_file.assert_called_once_with(filepath, 'w', newline='', encoding='utf-8')
    
    mock_writer.writeheader.assert_called_once()
    assert mock_writer.writerow.call_count == 2
    
    # Check the contents of the first call to writerow
    first_call_args = mock_writer.writerow.call_args_list[0].args[0]
    assert first_call_args['year'] == 2020
    assert first_call_args['state_name'] == "Testland"
    assert first_call_args['state_winner'] == "Democratic"

def test_save_to_csv_no_data(caplog):
    """Tests that the function handles empty input gracefully."""
    save_to_csv([], "some/path.csv")
    assert "No results to save to CSV" in caplog.text

@patch('src.data.processors.os.makedirs')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
def test_save_to_json_success(mock_json_dump, mock_file, mock_makedirs, sample_election_results):
    """Tests that save_to_json calls json.dump with the correct data structure."""
    filepath = "fake/data.json"
    save_to_json(sample_election_results, filepath)
    
    mock_makedirs.assert_called_once_with("fake", exist_ok=True)
    mock_file.assert_called_once_with(filepath, 'w', encoding='utf-8')
    
    # Check that json.dump was called
    mock_json_dump.assert_called_once()
    
    # Inspect the data passed to json.dump
    dumped_data = mock_json_dump.call_args.args[0]
    assert isinstance(dumped_data, list)
    assert len(dumped_data) == 2
    assert dumped_data[1]['state'] == "Pythania"
    assert dumped_data[1]['state_results']['winner'] == "Republican"

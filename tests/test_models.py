import pytest
from src.data.models import StateData, YearData, ElectionResult, Party

# --- Fixtures for reusable test objects ---

@pytest.fixture
def sample_state():
    """Provides a valid StateData instance."""
    return StateData(state_name="Testland", electoral_votes=10)

@pytest.fixture
def sample_year():
    """Provides a valid YearData instance."""
    return YearData(
        year=2020,
        dem_leader="Joe Test",
        rep_leader="Don Test",
        dem_votes="1,000,000",
        rep_votes=500000
    )

# --- Tests for StateData ---

def test_statedata_creation(sample_state):
    assert sample_state.state_name == "Testland"
    assert sample_state.electoral_votes == 10

def test_statedata_creation_no_ev():
    state = StateData(state_name="NoEVLand")
    assert state.state_name == "NoEVLand"
    assert state.electoral_votes is None

@pytest.mark.parametrize("name", [None, ""])
def test_statedata_invalid_name_raises_error(name):
    with pytest.raises(ValueError):
        StateData(state_name=name)

def test_statedata_invalid_ev_type_raises_error():
    with pytest.raises(TypeError):
        StateData(state_name="Testland", electoral_votes="ten")

# --- Tests for YearData ---

def test_yeardata_creation(sample_year):
    assert sample_year.year == 2020
    assert sample_year.dem_leader == "Joe Test"
    assert sample_year.rep_leader == "Don Test"
    # Tests vote cleaning logic
    assert sample_year.dem_votes == 1000000
    assert sample_year.rep_votes == 500000

def test_yeardata_invalid_year_raises_error():
    with pytest.raises(TypeError):
        YearData(year="2020")

def test_yeardata_total_national_votes_property(sample_year):
    assert sample_year.total_national_votes == 1500000

def test_yeardata_total_votes_is_none_if_incomplete():
    year_data = YearData(year=2024, dem_votes=100)
    assert year_data.total_national_votes is None

def test_yeardata_vote_cleaning_handles_invalid_string(caplog):
    year_data = YearData(year=2024, dem_votes="not a number")
    assert year_data.dem_votes is None
    assert "Could not parse vote string" in caplog.text

# --- Tests for ElectionResult ---

def test_electionresult_creation(sample_state, sample_year):
    result = ElectionResult(
        state_info=sample_state,
        year_info=sample_year,
        dem_percentage=55.5,
        rep_percentage=44.5,
        winner=Party.DEMOCRATIC
    )
    assert result.state_info.state_name == "Testland"
    assert result.year_info.year == 2020
    assert result.winner == Party.DEMOCRATIC

def test_electionresult_invalid_info_type_raises_error(sample_year):
    with pytest.raises(TypeError):
        ElectionResult(state_info="not a state object", year_info=sample_year)

@pytest.mark.parametrize("percent", ["55.5", "fifty-five"])
def test_electionresult_invalid_percentage_type_raises_error(sample_state, sample_year, percent):
    with pytest.raises(TypeError):
        ElectionResult(state_info=sample_state, year_info=sample_year, dem_percentage=percent)

def test_electionresult_out_of_range_percentage_logs_warning(sample_state, sample_year, caplog):
    ElectionResult(state_info=sample_state, year_info=sample_year, dem_percentage=105.0)
    assert "percentage 105.0 is outside the 0-100 range" in caplog.text

def test_electionresult_repr():
    state = StateData("Testland")
    year = YearData(2020)
    result = ElectionResult(state, year, winner=Party.REPUBLICAN)
    expected_repr = "ElectionResult(State='Testland', Year=2020, DEM%=None, REP%=None, Winner=Republican)"
    assert repr(result) == expected_repr
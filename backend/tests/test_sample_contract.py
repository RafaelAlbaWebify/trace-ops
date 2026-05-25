from app.config import FIRST_MODULE_ID, SUPPORTED_SAMPLE_SCENARIOS
from app.models import CollectorResult
from app.sample_loader import load_all_samples


def test_all_known_samples_are_present():
    samples = load_all_samples()

    assert set(samples.keys()) == set(SUPPORTED_SAMPLE_SCENARIOS)


def test_all_samples_match_collector_result_contract():
    samples = load_all_samples()

    for scenario, sample in samples.items():
        result = CollectorResult(**sample)

        assert result.scenario_id == scenario
        assert result.module == FIRST_MODULE_ID
        assert result.input.user_principal_name
        assert result.input.affected_service

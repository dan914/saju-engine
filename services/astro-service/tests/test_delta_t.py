from app.core.delta_t import DeltaTPolicy


def test_delta_t_policy_thresholds() -> None:
    policy = DeltaTPolicy.load()
    assert policy.thresholds["standard"] >= 5
    prefer, fallback = policy.select_source(1900)
    assert prefer is not None


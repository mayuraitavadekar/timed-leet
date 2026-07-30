import pytest

from timed_leet.session import (
    BRUTE_FORCE_CODE,
    END,
    OPTIMIZATION,
    Route,
    Session,
)


def test_standard_route_is_45_minutes() -> None:
    session = Session()
    assert session.total_duration == 45 * 60


def test_optional_route_is_51_minutes() -> None:
    session = Session()
    session.jump_to(BRUTE_FORCE_CODE.key)
    assert session.route is Route.WITH_BRUTE_FORCE_CODE
    assert session.total_duration == 51 * 60


def test_decision_occurs_after_first_11_minutes() -> None:
    session = Session()
    events = session.advance(11 * 60)
    assert events[-1] == "decision"
    assert session.awaiting_code_decision
    assert session.total_elapsed == 11 * 60


def test_no_choice_goes_directly_to_optimization() -> None:
    session = Session()
    session.advance(11 * 60)
    phase = session.choose_brute_force_code(False)
    assert phase is OPTIMIZATION
    assert session.total_elapsed == 11 * 60
    assert session.total_duration == 45 * 60


def test_yes_choice_adds_six_minutes() -> None:
    session = Session()
    session.advance(11 * 60)
    phase = session.choose_brute_force_code(True)
    assert phase is BRUTE_FORCE_CODE
    assert session.total_elapsed == 11 * 60
    assert session.total_duration == 51 * 60


def test_clicking_phase_resets_elapsed_to_its_route_start() -> None:
    session = Session()
    session.jump_to("code")
    assert session.current_phase.name == "Code"
    assert session.total_elapsed == 18 * 60

    session.jump_to(BRUTE_FORCE_CODE.key)
    session.jump_to("code")
    assert session.total_elapsed == 24 * 60


def test_full_standard_session_finishes_at_45_minutes() -> None:
    session = Session()
    session.advance(11 * 60)
    session.choose_brute_force_code(False)
    events = session.advance(34 * 60)
    assert "finished" in events
    assert session.current_phase is END
    assert session.total_elapsed == 45 * 60
    assert session.finished


def test_negative_time_is_rejected() -> None:
    with pytest.raises(ValueError):
        Session().advance(-1)


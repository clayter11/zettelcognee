"""DataPoints model tests."""

from app.parsers.datapoints import (
    DATAPOINT_MAP,
    Calculation,
    CommercialProposal,
    Contract,
    Drawing,
    MeetingNote,
)


def test_commercial_proposal():
    cp = CommercialProposal(
        client="ООО Альфа",
        project_name="Реконструкция",
        items=["Проектирование", "Монтаж"],
        total_price=2_500_000,
        currency="RUB",
    )
    assert cp.client == "ООО Альфа"
    assert cp.total_price == 2_500_000
    assert len(cp.items) == 2


def test_contract():
    c = Contract(
        parties=["ООО Альфа", "ООО Бета"],
        contract_number="ДП-2026/01",
        subject="Поставка оборудования",
        value=1_000_000,
    )
    assert len(c.parties) == 2
    assert c.contract_number == "ДП-2026/01"


def test_meeting_note():
    mn = MeetingNote(
        title="Совещание по проекту",
        date="2026-03-04",
        participants=["Иванов", "Петров"],
        decisions=["Утвердить смету"],
        action_items=["Подготовить КП до 10.03"],
        project="Реконструкция",
    )
    assert len(mn.participants) == 2
    assert len(mn.decisions) == 1


def test_datapoint_map():
    assert "proposal" in DATAPOINT_MAP
    assert "contract" in DATAPOINT_MAP
    assert "calculation" in DATAPOINT_MAP
    assert "drawing" in DATAPOINT_MAP
    assert "meeting" in DATAPOINT_MAP
    assert DATAPOINT_MAP["proposal"] is CommercialProposal

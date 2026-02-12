from datetime import date

from team_control import TeamControlStore, participation_for_date


def test_create_section_member_and_entries(tmp_path):
    store = TeamControlStore(str(tmp_path))
    section = store.create_section("Time Amarelo")
    member = store.add_member(section.id, "Fulano")

    store.set_entry(section.id, member.id, date(2026, 2, 6), "K")
    store.set_entry(section.id, member.id, date(2026, 2, 7), "")

    reloaded = TeamControlStore(str(tmp_path))
    assert len(reloaded.sections) == 1
    assert reloaded.sections[0].name == "Time Amarelo"
    assert reloaded.sections[0].members[0].entries.get("2026-02-06") == "K"
    assert "2026-02-07" not in reloaded.sections[0].members[0].entries


def test_limit_sections_to_ten(tmp_path):
    store = TeamControlStore(str(tmp_path))
    for i in range(10):
        store.create_section(f"Time {i}")

    try:
        store.create_section("Extra")
        assert False, "Deveria bloquear após 10 seções"
    except ValueError as e:
        assert "Limite" in str(e)


def test_participation_counts_k_and_p_only():
    assert participation_for_date(["", "A", "D"]) == 0
    assert participation_for_date(["K", "P", "A", "R"]) == 2


def test_store_scopes_teams_by_month_and_year(tmp_path):
    store = TeamControlStore(str(tmp_path))

    store.set_period(2026, 2)
    feb_team = store.create_section("Time Fevereiro")
    store.add_member(feb_team.id, "Maria")

    store.set_period(2026, 3)
    assert store.sections == []
    mar_team = store.create_section("Time Março")
    store.add_member(mar_team.id, "João")

    reloaded = TeamControlStore(str(tmp_path))
    reloaded.set_period(2026, 2)
    assert [s.name for s in reloaded.sections] == ["Time Fevereiro"]
    assert [m.name for m in reloaded.sections[0].members] == ["Maria"]

    reloaded.set_period(2026, 3)
    assert [s.name for s in reloaded.sections] == ["Time Março"]
    assert [m.name for m in reloaded.sections[0].members] == ["João"]

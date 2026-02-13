from datetime import date

from team_control import TeamControlStore, participation_for_date, build_team_control_report_rows, monthly_k_count, split_member_names


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



def test_report_rows_include_team_name_footer_and_monthly_participation(tmp_path):
    store = TeamControlStore(str(tmp_path))
    section = store.create_section("Time Azul")
    m = store.add_member(section.id, "Alice")
    store.set_entry(section.id, m.id, date(2026, 2, 2), "K")

    rows = build_team_control_report_rows(store.sections, 2026, 2)

    assert ["Time Azul"] in rows
    team_header_index = rows.index(["Time Azul"])
    names_header = rows[team_header_index + 1]
    assert names_header[0] == "Nome"

    section_rows = rows[team_header_index + 2 :]
    footer_index = next(i for i, row in enumerate(section_rows) if row and row[0] == "Participação")
    member_rows = section_rows[:footer_index]
    assert len(member_rows) == 1

    member_row = member_rows[0]
    assert member_row[-1] == "1"

    footer = section_rows[footer_index]
    assert footer[1] == ""  # 01/02/2026 (domingo sem preenchimento)
    assert footer[2] == "1"  # 02/02/2026
    assert footer[-1] == ""


def test_limit_members_to_twenty_per_team(tmp_path):
    store = TeamControlStore(str(tmp_path))
    section = store.create_section("Time Roxo")
    for i in range(20):
        store.add_member(section.id, f"Pessoa {i}")

    try:
        store.add_member(section.id, "Excedente")
        assert False, "Deveria bloquear após 20 funcionários"
    except ValueError as e:
        assert "20" in str(e)


def test_monthly_participation_counts_k_and_p(tmp_path):
    store = TeamControlStore(str(tmp_path))
    section = store.create_section("Time Verde")
    m = store.add_member(section.id, "Bruna")

    store.set_entry(section.id, m.id, date(2026, 2, 2), "K")
    store.set_entry(section.id, m.id, date(2026, 2, 3), "P")
    store.set_entry(section.id, m.id, date(2026, 2, 4), "A")

    assert monthly_k_count(m, 2026, 2) == 2


def test_split_member_names_supports_commas_and_new_lines():
    raw = "Octávio Mangabira Sobrinho,\nLewander Rodrigues Dias,\nCaio Coutinho Covos,\nRenato Augusto Dândalo"

    assert split_member_names(raw) == [
        "Octávio Mangabira Sobrinho",
        "Lewander Rodrigues Dias",
        "Caio Coutinho Covos",
        "Renato Augusto Dândalo",
    ]


def test_get_sections_for_period_returns_existing_periods(tmp_path):
    store = TeamControlStore(str(tmp_path))
    store.set_period(2026, 2)
    store.create_section("Time Fevereiro")

    store.set_period(2026, 3)
    store.create_section("Time Março")

    assert [s.name for s in store.get_sections_for_period(2026, 2)] == ["Time Fevereiro"]
    assert [s.name for s in store.get_sections_for_period(2026, 3)] == ["Time Março"]
    assert store.get_sections_for_period(2026, 4) == []


def test_copy_members_to_section_copies_to_target_month_and_year(tmp_path):
    store = TeamControlStore(str(tmp_path))

    store.set_period(2026, 2)
    source = store.create_section("Origem")
    store.add_member(source.id, "Alice")
    store.add_member(source.id, "Bruno")

    store.set_period(2026, 3)
    target = store.create_section("Destino")

    copied = store.copy_members_to_section(2026, 3, target.id, ["Alice", "Bruno"])
    assert copied == 2

    reloaded = TeamControlStore(str(tmp_path))
    reloaded.set_period(2026, 3)
    copied_names = [m.name for m in reloaded.sections[0].members]
    assert copied_names == ["Alice", "Bruno"]

    reloaded.set_period(2026, 2)
    source_names = [m.name for m in reloaded.sections[0].members]
    assert source_names == ["Alice", "Bruno"]


def test_to_payload_returns_json_serializable_structure(tmp_path):
    import json

    store = TeamControlStore(str(tmp_path))
    section = store.create_section("Time Serial")
    store.add_member(section.id, "Pessoa")

    payload = store.to_payload()

    assert json.loads(json.dumps(payload)) == payload
    period_key = store._period_key(date.today().year, date.today().month)
    assert payload["periods"][period_key]["sections"][0]["name"] == "Time Serial"


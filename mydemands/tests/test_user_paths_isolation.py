from mydemands.infra.paths import Paths


def test_user_id_and_dir_are_deterministic(tmp_path):
    paths = Paths(tmp_path)

    first = paths.user_id_from_email("User@Test.com")
    second = paths.user_id_from_email("user@test.com")

    assert first == second
    assert len(first) == 16
    assert paths.get_user_dir("user@test.com") == paths.get_user_dir("USER@test.com")


def test_user_directories_are_isolated(tmp_path):
    paths = Paths(tmp_path)
    user1_data = paths.user_data_dir("a@test.com")
    user2_data = paths.user_data_dir("b@test.com")

    assert user1_data != user2_data
    (user1_data / "data.csv").write_text("u1", encoding="utf-8")

    assert not (user2_data / "data.csv").exists()


def test_backup_and_export_dirs_use_current_user(tmp_path):
    paths = Paths(tmp_path)
    user_dir = paths.ensure_user_dirs("alpha@test.com")

    assert (user_dir / "backups").exists()
    assert (user_dir / "exports").exists()

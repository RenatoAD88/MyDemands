from mydemands.dashboard.layout_persistence_service import LayoutPersistenceService


def test_layout_persistence_restores_after_restart(tmp_path):
    service = LayoutPersistenceService(str(tmp_path))
    user = "ana@empresa.com"
    order = ["alertas", "graficos", "progresso", "big_numbers"]

    service.save(user, order)

    reloaded = LayoutPersistenceService(str(tmp_path))
    assert reloaded.load(user) == order

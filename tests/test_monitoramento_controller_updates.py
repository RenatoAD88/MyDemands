from mydemands.dashboard.controller import MonitoramentoController
from mydemands.dashboard.layout_persistence_service import LayoutPersistenceService
from mydemands.dashboard.metrics_service import DashboardMetricsService


class FakeStore:
    def __init__(self):
        self.rows = []

    def build_view(self):
        return list(self.rows)


class InMemoryLayout(LayoutPersistenceService):
    def __init__(self):
        self.saved = {}

    def load(self, user_email: str):
        return self.saved.get(user_email, ["big_numbers", "progresso", "graficos", "alertas"])

    def save(self, user_email: str, order):
        self.saved[user_email] = list(order)


def test_controller_updates_metrics_after_create_and_edit():
    store = FakeStore()
    controller = MonitoramentoController(store, DashboardMetricsService(), InMemoryLayout(), "user@x")

    store.rows = [{"_id": "1", "ID": "1", "Status": "Não iniciada", "Prioridade": "Alta", "Prazo": "", "Projeto": "P", "Descrição": "A"}]
    first = controller.load_metrics()
    assert first.total_demandas == 1
    assert first.concluidas == 0

    store.rows = [{"_id": "1", "ID": "1", "Status": "Concluído", "Prioridade": "Alta", "Prazo": "", "Projeto": "P", "Descrição": "A"}]
    second = controller.load_metrics()
    assert second.total_demandas == 1
    assert second.concluidas == 1
    assert second.concluidas_percentual == 100

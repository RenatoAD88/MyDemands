from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


@dataclass(frozen=True)
class WebScreen:
    id: str
    title: str
    source: str
    route: str
    kind: str


SCREEN_REGISTRY: tuple[WebScreen, ...] = (
    WebScreen("login", "Login", "mydemands.ui.login_window.LoginWindow", "/login", "dialog"),
    WebScreen("register", "Cadastro", "mydemands.ui.dialogs.register_dialog.RegisterDialog", "/register", "dialog"),
    WebScreen("forgot_password", "Esqueci a senha", "mydemands.ui.dialogs.forgot_password_dialog.ForgotPasswordDialog", "/forgot-password", "dialog"),
    WebScreen("reset_password", "Redefinir senha", "mydemands.ui.dialogs.reset_password_dialog.ResetPasswordDialog", "/reset-password", "dialog"),
    WebScreen("smtp_settings", "Configuração SMTP", "mydemands.ui.dialogs.smtp_settings_dialog.SmtpSettingsDialog", "/smtp-settings", "dialog"),
    WebScreen("passwords_registered", "Senhas cadastradas", "mydemands.ui.dialogs.passwords_registered_dialog.PasswordsRegisteredDialog", "/passwords-registered", "dialog"),
    WebScreen("master_settings", "Configurações mestre", "mydemands.ui.dialogs.master_settings_dialog.MasterSettingsDialog", "/master-settings", "dialog"),
    WebScreen("confirm_remember", "Confirmação lembrar acesso", "mydemands.ui.dialogs.confirm_remember_dialog.ConfirmRememberDialog", "/confirm-remember", "dialog"),
    WebScreen("main_window", "Aplicação principal", "app.MainWindow", "/", "window"),
    WebScreen("new_demand", "Nova demanda", "app.NewDemandDialog", "/new-demand", "dialog"),
    WebScreen("delete_demand", "Excluir demanda", "app.DeleteDemandDialog", "/delete-demand", "dialog"),
    WebScreen("date_pick", "Selecionar data", "app.DatePickDialog", "/date-pick", "dialog"),
    WebScreen("prazo_multi", "Prazo múltiplo", "app.PrazoMultiDialog", "/prazo-multi", "dialog"),
    WebScreen("add_team_member", "Adicionar membro do time", "app.AddTeamMemberDialog", "/add-team-member", "dialog"),
    WebScreen("copy_team_members", "Copiar membros do time", "app.CopyTeamMembersDialog", "/copy-team-members", "dialog"),
    WebScreen("delete_team_members", "Excluir membros do time", "app.DeleteTeamMembersDialog", "/delete-team-members", "dialog"),
    WebScreen("column_config", "Configurar colunas", "mydemands.dashboard.grid_widgets.ColumnConfigDialog", "/column-config", "dialog"),
    WebScreen("monitoramento", "Monitoramento", "mydemands.dashboard.view.MonitoramentoView", "/monitoramento", "tab"),
    WebScreen("eisenhower", "Matriz de Eisenhower", "mydemands.dashboard.eisenhower.EisenhowerView", "/eisenhower", "tab"),
    WebScreen("presencas_time", "Presenças do Time", "app.MainWindow tab", "/presencas-time", "tab"),
    WebScreen("consultar_pendentes", "Consultar Demandas Pendentes", "app.MainWindow tab", "/consultar-pendentes", "tab"),
    WebScreen("consultar_concluidas", "Consultar Demandas Concluídas", "app.MainWindow tab", "/consultar-concluidas", "tab"),
)


class WebMigrationHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/screens.json":
            payload = [screen.__dict__ for screen in SCREEN_REGISTRY]
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8")
            return

        screen = _find_screen(route)
        if screen:
            self._send_html(_render_screen(screen))
            return

        if route == "/health":
            self._send_html("<h1>ok</h1>")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Tela não encontrada")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, html: str, status: int = HTTPStatus.OK) -> None:
        self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8", status)

    def _send_bytes(self, body: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _find_screen(route: str) -> WebScreen | None:
    for screen in SCREEN_REGISTRY:
        if screen.route == route:
            return screen
    return None


def _render_screen(screen: WebScreen) -> str:
    links = "".join(
        f'<li><a href="{escape(item.route)}">{escape(item.title)}</a></li>'
        for item in SCREEN_REGISTRY
    )
    return f"""
<!doctype html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape(screen.title)} - MyDemands Web</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; }}
    header {{ background: #13294b; color: white; padding: 12px 20px; }}
    .container {{ display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }}
    nav {{ background: white; border-right: 1px solid #d8deea; padding: 16px; }}
    main {{ padding: 24px; }}
    .card {{ background: white; border: 1px solid #d8deea; border-radius: 10px; padding: 20px; }}
    li {{ margin-bottom: 8px; }}
  </style>
</head>
<body>
<header><strong>MyDemands Web</strong> · Migração de telas</header>
<div class=\"container\">
  <nav>
    <h3>Telas migradas</h3>
    <ul>{links}</ul>
  </nav>
  <main>
    <div class=\"card\">
      <h1>{escape(screen.title)}</h1>
      <p><strong>Tipo:</strong> {escape(screen.kind)}</p>
      <p><strong>Origem desktop:</strong> <code>{escape(screen.source)}</code></p>
      <p>Esta tela foi migrada para a versão web e pode ser acessada por rota dedicada.</p>
    </div>
  </main>
</div>
</body>
</html>
"""


def run(host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), WebMigrationHandler)
    return server


def main() -> None:
    server = run()
    print("MyDemands web ativo em http://0.0.0.0:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()

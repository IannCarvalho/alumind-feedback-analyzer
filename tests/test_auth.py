"""Testes da autenticação do dashboard.

Cobrem o fail-safe (sem senha => aberto), o gating das rotas web quando
há senha, o fluxo de login (senha certa/errada) e o logout. A rota da
API fica fora do escopo da auth de dashboard e permanece acessível.
"""
from unittest.mock import patch

import pytest

from app import create_app, db

from tests.helpers import login, post_form


@pytest.fixture()
def secured_client():
    """Client de um app com DASHBOARD_PASSWORD configurada (auth ligada)."""
    application = create_app()
    application.config.update(TESTING=True, DASHBOARD_PASSWORD="segredo")
    with application.app_context():
        db.create_all()
        yield application.test_client()
        db.session.remove()
        db.drop_all()


def test_dashboard_open_when_no_password(client):
    """Sem senha configurada, o dashboard responde sem redirecionar."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_dashboard_redirects_to_login_when_secured(secured_client):
    """Com senha, uma rota web protegida redireciona para o login."""
    resp = secured_client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_with_correct_password_grants_access(secured_client):
    """Senha correta autentica e dá acesso ao dashboard."""
    resp = login(secured_client, "segredo", follow_redirects=False)
    assert resp.status_code == 302
    # Depois do login, o dashboard responde 200.
    assert secured_client.get("/dashboard").status_code == 200


def test_login_with_wrong_password_is_rejected(secured_client):
    """Senha errada não autentica e mantém o dashboard bloqueado."""
    resp = login(secured_client, "errada", follow_redirects=True)
    assert resp.status_code == 200
    assert "Senha incorreta" in resp.get_data(as_text=True)
    # Ainda sem acesso.
    assert secured_client.get("/dashboard").status_code == 302


def test_logout_clears_session(secured_client):
    """Logout encerra a sessão e volta a bloquear o dashboard."""
    login(secured_client, "segredo")
    assert secured_client.get("/dashboard").status_code == 200

    post_form(secured_client, "/logout")
    assert secured_client.get("/dashboard").status_code == 302


def test_login_rejects_open_redirect(secured_client):
    """O parâmetro next só aceita caminhos locais (anti open-redirect)."""
    resp = post_form(
        secured_client,
        "/login?next=https://evil.example.com",
        {"password": "segredo"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/")


def test_api_route_not_gated_by_dashboard_auth(secured_client):
    """A API não é protegida pela auth do dashboard (contrato próprio)."""
    with patch("app.routes.api.feedback_analyzer"):
        # Request sem corpo válido => 400 da validação, NÃO 302 de login.
        resp = secured_client.post("/api/feedbacks", json={})
    assert resp.status_code != 302

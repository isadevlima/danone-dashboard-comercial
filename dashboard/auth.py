"""Autenticação do dashboard com sessão persistente via cookie."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import streamlit as st

COOKIE_NAME = "danone_dashboard_auth"
COOKIE_DAYS = 30
_PEPPER = "danone-ntr-dashboard-v1"


def _cookie_manager():
    """Singleton por sessão — não usar @st.cache_resource (CookieManager cria widgets)."""
    if "danone_cookie_mgr" not in st.session_state:
        import extra_streamlit_components as stx

        st.session_state.danone_cookie_mgr = stx.CookieManager(key="danone_cookie_mgr")
    return st.session_state.danone_cookie_mgr


def ler_senha_config() -> str | None:
    try:
        return st.secrets.get("dashboard", {}).get("senha")
    except Exception:
        return None


def _auth_token(senha: str) -> str:
    return hmac.new(senha.encode(), _PEPPER.encode(), hashlib.sha256).hexdigest()


def _sessao_valida(senha_cfg: str, cookies: dict) -> bool:
    return cookies.get(COOKIE_NAME) == _auth_token(senha_cfg)


def definir_autenticado(senha_cfg: str) -> None:
    st.session_state.autenticado = True
    _cookie_manager().set(
        COOKIE_NAME,
        _auth_token(senha_cfg),
        expires_at=datetime.now(timezone.utc) + timedelta(days=COOKIE_DAYS),
        key="auth_set_cookie",
    )


def encerrar_sessao() -> None:
    st.session_state.autenticado = False
    _cookie_manager().delete(COOKIE_NAME, key="auth_del_cookie")


def verificar_acesso() -> bool:
    """Retorna True se o usuário pode ver o dashboard."""
    senha_cfg = ler_senha_config()
    if not senha_cfg:
        return True

    if st.session_state.get("autenticado"):
        return True

    cookies = _cookie_manager().get_all()
    if cookies is None:
        # CookieManager ainda carregando do navegador — aguarda próximo rerun
        st.stop()

    if _sessao_valida(senha_cfg, cookies):
        st.session_state.autenticado = True
        return True

    st.markdown(
        """
        <div class="hero">
            <h1>Dashboard Comercial — Danone NTR</h1>
            <p>Acesso restrito · Digite a senha fornecida pelo responsável</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        senha = st.text_input("Senha", type="password", placeholder="Senha de acesso")
        if st.button("Entrar", type="primary", use_container_width=True):
            if senha == senha_cfg:
                definir_autenticado(senha_cfg)
                st.rerun()
            else:
                st.error("Senha incorreta.")
    return False


def render_botao_sair() -> None:
    """Botão de logout na sidebar (só quando há senha configurada)."""
    if not ler_senha_config() or not st.session_state.get("autenticado"):
        return
    if st.sidebar.button("Sair", use_container_width=True, key="btn_logout"):
        encerrar_sessao()
        st.rerun()

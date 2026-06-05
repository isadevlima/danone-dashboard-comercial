"""Autenticação do dashboard com sessão persistente via cookie."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import streamlit as st

COOKIE_NAME = "danone_dashboard_auth"
COOKIE_DAYS = 30
_PEPPER = "danone-ntr-dashboard-v1"
_COOKIE_KEY = "danone_cookie_mgr"


def _cookie_manager():
    """Nova instância a cada rerun — mesma key reconecta ao componente no navegador."""
    import extra_streamlit_components as stx

    return stx.CookieManager(key=_COOKIE_KEY)


def ler_senha_config() -> str | None:
    try:
        return st.secrets.get("dashboard", {}).get("senha")
    except Exception:
        return None


def _auth_token(senha: str) -> str:
    return hmac.new(senha.encode(), _PEPPER.encode(), hashlib.sha256).hexdigest()


def _token_do_cookie() -> str | None:
    return _cookie_manager().get(COOKIE_NAME)


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
    st.session_state.pop("_auth_cookie_check_done", None)
    _cookie_manager().delete(COOKIE_NAME, key="auth_del_cookie")


def verificar_acesso() -> bool:
    """Retorna True se o usuário pode ver o dashboard."""
    senha_cfg = ler_senha_config()
    if not senha_cfg:
        return True

    if st.session_state.get("autenticado"):
        return True

    token_cookie = _token_do_cookie()
    if token_cookie == _auth_token(senha_cfg):
        st.session_state.autenticado = True
        return True

    # Primeira passagem: componente de cookie ainda sincronizando com o navegador
    if not st.session_state.get("_auth_cookie_check_done"):
        st.session_state._auth_cookie_check_done = True
        st.stop()

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
    """Botão de logout no rodapé da sidebar."""
    if not ler_senha_config() or not st.session_state.get("autenticado"):
        return
    st.sidebar.divider()
    if st.sidebar.button("Sair", use_container_width=True, key="btn_logout"):
        encerrar_sessao()
        st.rerun()

"""Formatação de valores para dashboard, slides e relatórios."""


def fmt_moeda(valor: float, compacto: bool = False) -> str:
    if compacto:
        if abs(valor) >= 1e9:
            return f"R$ {valor / 1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
        if abs(valor) >= 1e6:
            return f"R$ {valor / 1e6:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def fmt_pct(valor: float | None, com_sinal: bool = True) -> str:
    if valor is None:
        return "—"
    pct = valor * 100
    texto = f"{pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if com_sinal and pct > 0:
        return f"+{texto}%"
    return f"{texto}%"


def fmt_ms(valor: float | None) -> str:
    return fmt_pct(valor, com_sinal=False)


def fmt_numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def fmt_produto_curto(nome: str, max_len: int = 42) -> str:
    substituicoes = {
        "800.0 G X 1": "800G",
        "800.0 G": "800G",
        " PO ": " ",
    }
    curto = nome
    for antigo, novo in substituicoes.items():
        curto = curto.replace(antigo, novo)
    curto = " ".join(curto.split())
    if len(curto) > max_len:
        return curto[: max_len - 1] + "…"
    return curto

from decimal import Decimal, ROUND_HALF_UP

ALIQUOTA_INTERNA = Decimal("18.00")
ALIQUOTA_INTERESTADUAL = Decimal("7.00")


def function_aliquota(uf_origem, uf_destino):
    if str(uf_origem).strip().upper() == str(uf_destino).strip().upper():
        return float(ALIQUOTA_INTERNA)
    return float(ALIQUOTA_INTERESTADUAL)


def calcular_icms(linha):
    uf_origem = str(linha["uf_origem"]).strip().upper()
    uf_destino = str(linha["uf_destino"]).strip().upper()
    if uf_origem == uf_destino:
        aliquota = ALIQUOTA_INTERNA
    else:
        aliquota = ALIQUOTA_INTERESTADUAL
    base = Decimal(linha["valor_base"])
    valor_icms = (base * aliquota / Decimal("100")).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    valor_total = (base + valor_icms).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    atual = Decimal(linha["valor_icms"])
    incorreto = abs(float(linha["aliquota_icms"]) - float(aliquota)) > 0.001
    return {
        "aliquota": aliquota,
        "valor_icms": valor_icms,
        "valor_total": valor_total,
        "atual": atual,
        "incorreto": incorreto,
    }


def formatar_moeda(valor):
    v = float(valor)
    inteiro, decimal_ = f"{abs(v):.2f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    sinal = "-" if v < 0 else ""
    return f"R$ {sinal}{inteiro},{decimal_}"


def formatar_numero(valor):
    return f"{float(valor):.2f}".replace(".", ",")
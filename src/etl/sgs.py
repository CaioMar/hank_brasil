"""Download SGS observations and initialize a historical HANK simulation."""

import argparse
import calendar
from datetime import date
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import polars as pl


SERIES = {
    "selic": 432,
    "ipca": 433,
    "divida_pib": 13762,
    "reservas": 13621,
    "cambio": 1,
}
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


def mes_anterior(mes, quantidade=1):
    indice = mes.year * 12 + mes.month - 1 - quantidade
    return date(indice // 12, indice % 12 + 1, 1)


def baixar_serie(codigo, inicio, fim):
    if inicio > fim:
        raise ValueError("A data inicial deve preceder a data final.")
    registros = []
    atual = inicio
    while atual <= fim:
        limite = min(date(atual.year, 12, 31), fim)
        parametros = urlencode({
            "formato": "json",
            "dataInicial": atual.strftime("%d/%m/%Y"),
            "dataFinal": limite.strftime("%d/%m/%Y"),
        })
        try:
            with urlopen(f"{URL.format(codigo=codigo)}?{parametros}", timeout=30) as resposta:
                dados = json.load(resposta)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as erro:
            raise RuntimeError(f"Falha ao baixar a série SGS {codigo}: {erro}") from erro
        if not isinstance(dados, list):
            raise ValueError(f"Resposta inválida para a série SGS {codigo}: {dados}")
        for item in dados:
            try:
                dia, mes, ano = map(int, item["data"].split("/"))
                valor = float(item["valor"])
                if not float("-inf") < valor < float("inf"):
                    raise ValueError("valor não finito")
                registros.append((date(ano, mes, dia), valor))
            except (KeyError, TypeError, ValueError) as erro:
                raise ValueError(f"Observação inválida na série SGS {codigo}: {item}") from erro
        atual = date(limite.year + 1, 1, 1)
    return pl.DataFrame(registros, schema={"data": pl.Date, "valor": pl.Float64}, orient="row")


def baixar_historico(inicio, fim):
    if inicio.day != 1 or fim.day != 1 or inicio > fim:
        raise ValueError("Informe meses válidos, com início não posterior ao fim.")
    ultimo_dia = date(fim.year, fim.month, calendar.monthrange(fim.year, fim.month)[1])
    if ultimo_dia >= date.today():
        raise ValueError("O mês final deve estar encerrado.")
    tabelas = []
    for nome, codigo in SERIES.items():
        dados = baixar_serie(codigo, mes_anterior(inicio, 11) if nome == "ipca" else inicio, ultimo_dia)
        mensal = (dados.sort("data")
                  .with_columns(pl.col("data").dt.truncate("1mo").alias("mes"))
                  .group_by("mes").agg(pl.col("valor").last().alias(nome)))
        tabelas.append(mensal)
    historico = tabelas[0]
    for tabela in tabelas[1:]:
        historico = historico.join(tabela, on="mes", how="full", coalesce=True)
    return historico.sort("mes")


def preparar_historico(historico, inicio, fim):
    meses = []
    atual = mes_anterior(inicio, 11)
    while atual <= fim:
        meses.append(atual)
        atual = date(atual.year + (atual.month == 12), atual.month % 12 + 1, 1)
    dados = pl.DataFrame({"mes": meses}, schema={"mes": pl.Date}).join(historico, on="mes", how="left")
    if dados["mes"].n_unique() != dados.height:
        raise ValueError("Há observações mensais duplicadas.")
    if dados["ipca"].null_count() or dados.filter(pl.col("ipca") <= -100).height:
        raise ValueError("IPCA ausente ou inválido na janela de 12 meses.")
    dados = dados.with_columns(
        ((1 + pl.col("ipca") / 100).rolling_map(lambda valores: valores.product(), window_size=12) - 1)
        .mul(100).alias("ipca_12m")
    ).filter(pl.col("mes") >= inicio)
    for nome in SERIES:
        if dados[nome].null_count():
            raise ValueError(f"Série {nome} incompleta no período solicitado.")
    if dados.filter((pl.col("divida_pib") <= 0) | (pl.col("cambio") <= 0) | (pl.col("reservas") < 0)).height:
        raise ValueError("Dívida, câmbio ou reservas apresentam valores inválidos.")
    return dados


def calibrar_inicial(historico):
    if historico.is_empty():
        raise ValueError("Histórico vazio.")
    inicial = historico.sort("mes").row(0, named=True)
    selic = inicial["selic"] / 100
    return {
        "selic_inicial": selic,
        "divida_inicial": inicial["divida_pib"],
        "cambio_inicial": inicial["cambio"],
        "inflacao_inicial": inicial["ipca_12m"] / 100,
        "reservas_iniciais": inicial["reservas"] / 1000,
        "juros_legados_iniciais": selic,
        "juros_efetivos_iniciais": selic,
        "selic_referencia_cambio": selic,
    }


def simular_historico(historico, parametros, n_agentes=100_000):
    import jax.numpy as jnp
    from simulacao_hank_brasil import criar_simulador_jax, gerar_populacao_agentes

    if n_agentes < 10 or n_agentes % 10:
        raise ValueError("O número de agentes deve ser um múltiplo de 10, de pelo menos 10.")
    observacoes = historico.sort("mes").slice(1)
    if observacoes.is_empty():
        raise ValueError("O backtest requer pelo menos dois meses.")
    agentes = gerar_populacao_agentes(n_agentes, divida_inicial=parametros["divida_inicial"])
    simular = criar_simulador_jax(*agentes, parametros=parametros)
    selic = jnp.asarray(observacoes["selic"].to_numpy() / 100)
    zeros = jnp.zeros_like(selic)
    resultados = simular(selic, zeros, zeros, zeros, uso_reservas_bc=0.0)
    nomes = ("pib_real_simulado", "divida_pib_simulada", "resultado_primario_simulado",
             "juros_pib_simulados", "inflacao_anual_simulada", "cambio_simulado", "desigualdade_simulada")
    return observacoes.with_columns([pl.Series(nome, valor.tolist()) for nome, valor in zip(nomes, resultados)])


def parse_mes(valor):
    try:
        return date.fromisoformat(valor + "-01")
    except ValueError as erro:
        raise argparse.ArgumentTypeError("Use o formato AAAA-MM.") from erro


def main():
    parser = argparse.ArgumentParser(description="Calibração inicial e comparação histórica com dados SGS.")
    parser.add_argument("--inicio", type=parse_mes, required=True, help="Mês inicial, AAAA-MM")
    parser.add_argument("--fim", type=parse_mes, required=True, help="Último mês encerrado, AAAA-MM")
    parser.add_argument("--agentes", type=int, default=100_000)
    parser.add_argument("--saida", type=Path, default=Path("data/sgs"))
    args = parser.parse_args()
    if args.inicio >= args.fim:
        parser.error("O fim deve ser posterior ao mês inicial.")
    historico_bruto = baixar_historico(args.inicio, args.fim)
    historico = preparar_historico(historico_bruto, args.inicio, args.fim)
    parametros = calibrar_inicial(historico)
    comparacao = simular_historico(historico, parametros, args.agentes)
    args.saida.mkdir(parents=True, exist_ok=True)
    historico_bruto.write_parquet(args.saida / "historico_bruto.parquet")
    historico.write_parquet(args.saida / "historico_mensal.parquet")
    comparacao.write_parquet(args.saida / "backtest.parquet")
    (args.saida / "parametros.json").write_text(json.dumps(parametros, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Dados, parâmetros e comparação salvos em {args.saida}")
    print(comparacao.select("mes", "divida_pib", "divida_pib_simulada", "ipca_12m", "inflacao_anual_simulada", "cambio", "cambio_simulado"))


if __name__ == "__main__":
    main()
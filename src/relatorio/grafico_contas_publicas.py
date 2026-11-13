"""Gera dados e gráficos anuais de contas públicas e Selic a partir do SGS."""

from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import openpyxl
import polars as pl

from src.etl.sgs import baixar_serie


SERIES = {"primario": 5793, "juros": 5760, "nominal": 5727, "selic": 432}
INICIO = date(2015, 1, 1)
FIM = date(2025, 12, 31)
RAIZ = Path(__file__).resolve().parents[2]
TESOURO = "https://www.tesourotransparente.gov.br/ckan/dataset/ab56485b-9c40-4efb-8563-9ce3e1973c4b/resource/527ccdb1-3059-42f3-bf23-b5e3ab4c6dc6/download/seriehistoricajul26.xlsx"


def obter_dados():
    tabelas = []
    for nome, codigo in SERIES.items():
        mensal = (baixar_serie(codigo, INICIO, FIM)
                  .sort("data")
                  .with_columns(pl.col("data").dt.truncate("1mo").alias("mes"))
                  .group_by("mes").agg(pl.col("valor").last().alias(nome)))
        tabelas.append(mensal)
    dados = tabelas[0]
    for tabela in tabelas[1:]:
        dados = dados.join(tabela, on="mes", how="full", coalesce=True)
    dados = dados.sort("mes")
    if dados.height != 132 or any(dados[nome].null_count() for nome in SERIES):
        raise ValueError("Séries fiscais ou Selic incompletas entre 2015 e 2025.")
    if dados.select((pl.col("nominal") - pl.col("primario") - pl.col("juros")).abs().max()).item() > 0.02:
        raise ValueError("As séries não satisfazem a identidade fiscal dentro do arredondamento.")
    return dados.filter(pl.col("mes").dt.month() == 12).with_columns(pl.col("mes").dt.year().alias("ano"))


def obter_contas_tesouro():
    with urlopen(TESOURO, timeout=60) as resposta:
        planilha = openpyxl.load_workbook(BytesIO(resposta.read()), read_only=True, data_only=True)
    try:
        aba = planilha["2.1"]
        linhas = list(aba.iter_rows(values_only=True))
        if "R$ Milhões - Valores Correntes" not in linhas[2]:
            raise ValueError("Unidade inesperada na planilha do Tesouro.")
        anos = {valor: indice for indice, valor in enumerate(linhas[4]) if isinstance(valor, int)}
        receitas = next(linha for linha in linhas if linha[0] == "3. RECEITA LÍQUIDA  (1-2)")
        despesas = next(linha for linha in linhas if linha[0] == "4. DESPESA TOTAL")
        contas = pl.DataFrame([
            {"ano": ano, "receita_milhoes": receitas[anos[ano]], "despesa_milhoes": despesas[anos[ano]]}
            for ano in range(2015, 2026)
        ])
    finally:
        planilha.close()
    pib = (baixar_serie(1207, INICIO, FIM)
           .with_columns(pl.col("data").dt.year().alias("ano"), (pl.col("valor") / 1_000_000).alias("pib_milhoes"))
           .select("ano", "pib_milhoes"))
    contas = contas.join(pib, on="ano", how="left")
    if contas.height != 11 or contas.null_count().row(0) != (0, 0, 0, 0) or contas.filter(pl.col("pib_milhoes") <= 0).height:
        raise ValueError("Dados anuais do Tesouro ou do PIB incompletos.")
    return contas.with_columns(
        (100 * pl.col("receita_milhoes") / pl.col("pib_milhoes")).alias("receita_primaria_gc"),
        (100 * pl.col("despesa_milhoes") / pl.col("pib_milhoes")).alias("despesa_primaria_gc"),
    ).select("ano", "receita_primaria_gc", "despesa_primaria_gc")


def main():
    dados = obter_dados().join(obter_contas_tesouro(), on="ano", how="inner").sort("ano")
    if dados.height != 11:
        raise ValueError("As séries do Banco Central e do Tesouro não cobrem todos os anos.")
    dados.select("ano", *SERIES, "receita_primaria_gc", "despesa_primaria_gc").write_csv(RAIZ / "docs/contas-publicas.csv")
    figura, eixos = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    for eixo in eixos:
        eixo.set_facecolor("#f5f7f4")
        eixo.grid(axis="y", color="#d5ded8", linewidth=0.8)
        eixo.set_axisbelow(True)
        eixo.tick_params(colors="#50645d", length=0, pad=8)
        for borda in eixo.spines.values():
            borda.set_visible(False)
    anos = dados["ano"].to_list()
    for coluna, cor, rotulo in (("primario", "#14675a", "Déficit primário"),
                                 ("juros", "#b36a2d", "Juros nominais"),
                                 ("nominal", "#a64431", "Déficit nominal")):
        eixos[0].plot(anos, dados[coluna].to_list(), marker="o", color=cor, linewidth=2.5, label=rotulo)
    eixos[0].axhline(0, color="#53665e", linewidth=0.8)
    eixos[0].set_ylabel("Acumulado em 12 meses\n(% do PIB)")
    eixos[0].legend(frameon=False, loc="upper left", ncol=3)
    eixos[1].plot(anos, dados["selic"].to_list(), marker="o", color="#315d83", linewidth=2.5)
    eixos[1].set_ylabel("Meta Selic em dezembro\n(% ao ano)")
    eixos[1].set_xticks(anos)
    figura.savefig(RAIZ / "docs/grafico-contas-publicas.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)

    figura, eixo = plt.subplots(figsize=(11, 4), layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    for coluna, cor, rotulo in (("receita_primaria_gc", "#315d83", "Receita líquida"),
                                 ("despesa_primaria_gc", "#14675a", "Despesa primária")):
        eixo.plot(anos, dados[coluna].to_list(), marker="o", color=cor, linewidth=2.5, label=rotulo)
    eixo.set_ylabel("Governo central (% do PIB)")
    eixo.set_xticks(anos)
    eixo.grid(axis="y", color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    eixo.legend(frameon=False, loc="upper left", ncol=2)
    figura.savefig(RAIZ / "docs/grafico-gasto-primario.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)
    print(dados.select("ano", *SERIES, "receita_primaria_gc", "despesa_primaria_gc"))


if __name__ == "__main__":
    main()
"""Diagnóstico reproduzível da comparação histórica e dos fluxos do modelo."""

import argparse
import json
from pathlib import Path
import shlex

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import polars as pl

from src.etl.sgs import calibrar_inicial, simular_historico


def calcular_diagnostico(dados):
    dados = dados.sort("mes").with_columns(
        pl.col("pib_nominal").shift(1).fill_null(100.0).alias("pib_nominal_anterior"),
        (pl.col("divida_pib_simulada") - pl.col("divida_pib")).alias("erro_divida_pp"),
        (pl.col("cambio_simulado") - pl.col("cambio")).alias("erro_cambio"),
    ).with_columns(
        (100 * pl.col("juros_nominais_anualizados") / (12 * pl.col("pib_nominal"))).alias("contribuicao_juros_pp"),
        (-100 * pl.col("primario_nominal_anualizado") / (12 * pl.col("pib_nominal"))).alias("contribuicao_primario_pp"),
        (100 * pl.col("divida_anterior") * (1 / pl.col("pib_nominal") - 1 / pl.col("pib_nominal_anterior"))).alias("contribuicao_pib_nominal_pp"),
        (pl.col("arrecadacao_anualizada") - pl.col("imposto_trabalho_anualizado") - pl.col("imposto_topo_anualizado") - pl.col("isencoes_anualizadas")).alias("arrecadacao_sem_contrapartida_anualizada"),
        (pl.col("juros_nominais_anualizados") - pl.col("juros_familias_anualizados")).alias("diferenca_juros_anualizada"),
    )
    return dados


def gerar_relatorio(dados, parametros, agentes, diretorio_dados="data/sgs", diretorio_saida="data/sgs"):
    ultimo = dados.row(-1, named=True)
    primeiro = dados.row(0, named=True)
    divida_inicial = parametros["divida_inicial"]
    totais = dados.select(
        pl.col("erro_divida_pp").mean().alias("vies_divida"),
        pl.col("erro_divida_pp").abs().mean().alias("mae_divida"),
        (pl.col("erro_divida_pp").pow(2).mean().sqrt()).alias("rmse_divida"),
        pl.col("erro_cambio").mean().alias("vies_cambio"),
        pl.col("erro_cambio").abs().mean().alias("mae_cambio"),
        pl.col("contribuicao_juros_pp").sum().alias("juros"),
        pl.col("contribuicao_primario_pp").sum().alias("primario"),
        pl.col("contribuicao_pib_nominal_pp").sum().alias("pib"),
        pl.col("ajuste_piso_riqueza").sum().alias("piso"),
        pl.col("ajuste_normalizacao_riqueza").sum().alias("normalizacao"),
        (pl.col("arrecadacao_sem_contrapartida_anualizada") / 12).sum().alias("tributos"),
        (pl.col("diferenca_juros_anualizada").abs() / 12).sum().alias("diferenca_juros"),
    ).row(0, named=True)
    variacao = ultimo["divida_pib_simulada"] - divida_inicial
    residual = variacao - totais["juros"] - totais["primario"] - totais["pib"]
    return f"""# Diagnóstico histórico e auditoria contábil

## Escopo

Exercício condicional de {primeiro['mes']:%m/%Y} a {ultimo['mes']:%m/%Y}, com {dados.height} meses e {agentes:,} agentes sintéticos. O mês anterior inicializa o modelo com dívida/PIB de {divida_inicial:.2f}%. A Selic futura realizada é usada como entrada; não é uma previsão em tempo real nem um teste fora da amostra. Dados do SGS podem ter sido revisados e datas de divulgação não foram verificadas.

## Erros históricos

| Indicador | Simulado final | Observado final | Viés médio | Erro absoluto médio | RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dívida/PIB (p.p. para erros) | {ultimo['divida_pib_simulada']:.2f}% | {ultimo['divida_pib']:.2f}% | {totais['vies_divida']:.2f} | {totais['mae_divida']:.2f} | {totais['rmse_divida']:.2f} |
| Câmbio (R$/US$) | {ultimo['cambio_simulado']:.4f} | {ultimo['cambio']:.4f} | {totais['vies_cambio']:.4f} | {totais['mae_cambio']:.4f} | — |

O erro é simulado menos observado. Inflação anualizada instantânea simulada ({ultimo['inflacao_anual_simulada']:.2f}% no último mês) e IPCA observado acumulado em 12 meses ({ultimo['ipca_12m']:.2f}%) não são a mesma medida; não são usados aqui para calcular erros de previsão.

![Erro mensal da dívida e comparação do câmbio](diagnostico_graficos.png)

## Decomposição da dívida simulada

Contribuições acumuladas para a variação da dívida/PIB, em pontos percentuais, segundo a identidade do próprio modelo:

| Componente | p.p. |
| --- | ---: |
| Juros | {totais['juros']:+.3f} |
| Resultado primário (superávit reduz a dívida) | {totais['primario']:+.3f} |
| Variação do PIB nominal no denominador | {totais['pib']:+.3f} |
| Residual numérico | {residual:+.6f} |
| Variação total simulada | {variacao:+.3f} |

A decomposição usa o PIB nominal corrente para juros e resultado primário e o estoque anterior para o efeito do denominador. Ela explica a trajetória **simulada**, não decompõe a dívida observada nem identifica as causas do erro.

## Auditoria de fluxos e estoques

Unidades abaixo são nominais, na escala em que o PIB inicial é 100; fluxos anualizados são divididos por 12 antes de acumular. Não são valores em reais nem parcelas constantes do PIB.

- Ajuste acumulado pelo piso zero da riqueza: {totais['piso']:+.4f}.
- Ajuste acumulado pela normalização da riqueza à dívida: {totais['normalizacao']:+.4f}. Esse ajuste altera a riqueza além da poupança calculada; igualar estoques não prova consistência fluxo-estoque.
- Arrecadação pública acumulada sem contrapartida nos impostos de famílias explicitamente modelados: {totais['tributos']:+.4f}. A arrecadação de base é calculada sobre o PIB nominal corrente, enquanto o imposto explícito das famílias incide sobre a renda do trabalho do período anterior.
- Diferença absoluta acumulada entre juros pagos pelo governo e recebidos pelas famílias: {totais['diferenca_juros']:.6f}; pequenas diferenças refletem a regularização numérica usada no denominador.
- O gasto primário total não é distribuído integralmente como renda ou transferência às famílias no modelo; tampouco há balanços explícitos de empresas, setor externo e banco central. A revisão de isenções eleva a receita pública sem débito correspondente nas famílias. Por isso, não é possível demonstrar fechamento setorial completo.

## Interpretação e próximos passos

Os dados não demonstram que uma política específica causou o desvio. Antes de estimar elasticidades ou comparar com o Focus, é necessário definir as contrapartidas setoriais, corrigir os fluxos sem impor igualdade artificial de estoques e validar as identidades com testes. Depois, incorporar microdados e séries fiscais com suas datas de divulgação, e separar calibração e avaliação fora da amostra. A PMC não é identificada simplesmente a partir do consumo observado.

Reprodução: `python -m src.relatorio.diagnostico --dados {shlex.quote(str(diretorio_dados))} --agentes {agentes} --saida {shlex.quote(str(diretorio_saida))}`.
"""


def salvar_graficos(dados, destino):
    meses = dados["mes"].to_list()
    figura, eixos = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
    eixos[0].plot(meses, dados["erro_divida_pp"].to_list(), color="#b8523d")
    eixos[0].axhline(0, color="#52665e", linewidth=0.8)
    eixos[0].set_title("Dívida/PIB: erro mensal (simulado − observado)")
    eixos[0].set_ylabel("Pontos percentuais")
    eixos[1].plot(meses, dados["cambio"].to_list(), label="Observado · SGS", color="#14675a")
    eixos[1].plot(meses, dados["cambio_simulado"].to_list(), label="Simulado", color="#b8523d")
    eixos[1].set_title("Câmbio")
    eixos[1].set_ylabel("R$/US$")
    eixos[1].legend(frameon=False)
    for eixo in eixos:
        eixo.xaxis.set_major_locator(mdates.YearLocator())
        eixo.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        eixo.grid(axis="y", alpha=0.25)
    figura.savefig(destino, dpi=150)
    plt.close(figura)


def main():
    parser = argparse.ArgumentParser(description="Auditar a simulação histórica salva.")
    parser.add_argument("--dados", type=Path, default=Path("data/sgs"))
    parser.add_argument("--saida", type=Path, default=Path("data/sgs"))
    parser.add_argument("--agentes", type=int, default=100_000)
    args = parser.parse_args()
    historico = pl.read_parquet(args.dados / "historico_mensal.parquet")
    parametros = calibrar_inicial(historico)
    salvos = json.loads((args.dados / "parametros.json").read_text(encoding="utf-8"))
    if parametros != salvos:
        raise ValueError("Os parâmetros salvos não correspondem ao histórico.")
    auditoria = calcular_diagnostico(simular_historico(historico, parametros, args.agentes, auditoria=True))
    referencia = pl.read_parquet(args.dados / "backtest.parquet").sort("mes")
    if referencia["mes"].to_list() != auditoria["mes"].to_list() or (referencia["divida_pib_simulada"] - auditoria["divida_pib_simulada"]).abs().max() > 0.001:
        raise ValueError("A simulação não reproduz o backtest salvo; confira dados e número de agentes.")
    args.saida.mkdir(parents=True, exist_ok=True)
    auditoria.write_parquet(args.saida / "auditoria_mensal.parquet")
    salvar_graficos(auditoria, args.saida / "diagnostico_graficos.png")
    (args.saida / "diagnostico.md").write_text(
        gerar_relatorio(auditoria, parametros, args.agentes, args.dados, args.saida), encoding="utf-8"
    )
    print(f"Auditoria mensal e relatório gerados em {args.saida}")


if __name__ == "__main__":
    main()
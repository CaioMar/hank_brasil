"""Executa o protótipo SFC com trajetórias históricas condicionais do SGS."""

import argparse
from pathlib import Path

import jax.numpy as jnp
import polars as pl

from simulacao_hank_brasil import gerar_populacao_agentes
from src.etl.sgs import calibrar_inicial
from src.models.sfc import criar_simulador_sfc


def executar(historico, agentes=100_000, ancorar_pib=False):
    if agentes < 10 or agentes % 10:
        raise ValueError("O número de agentes deve ser um múltiplo de 10, de pelo menos 10.")
    historico = historico.sort("mes")
    if historico.height < 2:
        raise ValueError("O experimento requer pelo menos dois meses.")
    parametros = calibrar_inicial(historico)
    decil, renda, pmc, ativos = gerar_populacao_agentes(agentes, divida_inicial=parametros["divida_inicial"])
    gasto_privado_autonomo = 0.0
    if ancorar_pib:
        renda_inicial = 0.675 * renda + parametros["selic_inicial"] * ativos
        consumo_inicial = jnp.sum(pmc * jnp.maximum(renda_inicial, 0.0) + 0.032 * jnp.maximum(ativos, 0.0))
        gasto_privado_autonomo = float(100.0 - 32.9 - consumo_inicial)
        if gasto_privado_autonomo < 0:
            raise ValueError("A hipótese de ancoragem exige gasto privado autônomo não negativo.")
    simulador = criar_simulador_sfc(renda, pmc, ativos, decil, parametros["divida_inicial"], parametros["selic_inicial"], gasto_privado_autonomo=gasto_privado_autonomo)
    observacoes = historico.slice(1)
    selic = jnp.asarray(observacoes["selic"].to_numpy() / 100)
    inflacao_anualizada = jnp.asarray(observacoes["ipca"].to_numpy() * 12 / 100)
    zeros = jnp.zeros_like(selic)
    resultado = simulador(selic, zeros, zeros, zeros, inflacao_anualizada)
    return observacoes.with_columns([pl.Series(f"sfc_{nome}", valor.tolist()) for nome, valor in resultado.items()])


def main():
    parser = argparse.ArgumentParser(description="Comparação histórica condicional do protótipo SFC.")
    parser.add_argument("--dados", type=Path, default=Path("data/sgs"))
    parser.add_argument("--saida", type=Path, default=Path("data/sgs/experimento_sfc.parquet"))
    parser.add_argument("--agentes", type=int, default=100_000)
    parser.add_argument("--ancorar-pib", action="store_true", help="Adicionar gasto privado hipotético para PIB inicial 100.")
    args = parser.parse_args()
    historico = pl.read_parquet(args.dados / "historico_mensal.parquet")
    resultado = executar(historico, args.agentes, args.ancorar_pib)
    resumo = resultado.select(
        (pl.col("sfc_divida_pib") - pl.col("divida_pib")).last().alias("erro_final_pp"),
        pl.col("sfc_residual_ativos_divida").abs().max().alias("max_residual_ativos_divida"),
        pl.col("sfc_residual_juros").abs().max().alias("max_residual_juros_anual"),
    )
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    resultado.write_parquet(args.saida)
    print(resumo)
    print(f"Experimento salvo em {args.saida}")


if __name__ == "__main__":
    main()
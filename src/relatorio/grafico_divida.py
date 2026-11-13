"""Gera o gráfico da comparação histórica a partir do Parquet do SGS."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import polars as pl


def main():
    raiz = Path(__file__).resolve().parents[2]
    dados = pl.read_parquet(raiz / "data/sgs/backtest.parquet").sort("mes")
    fig, eixo = plt.subplots(figsize=(11, 4.4), layout="constrained")
    fig.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    eixo.plot(dados["mes"].to_list(), dados["divida_pib"].to_list(), color="#14675a", linewidth=3, label="Observada · SGS")
    eixo.plot(dados["mes"].to_list(), dados["divida_pib_simulada"].to_list(), color="#b8523d", linewidth=3, label="Simulada · HANK Brasil")
    eixo.set_ylabel("Dívida bruta / PIB (%)", color="#243833")
    eixo.xaxis.set_major_locator(mdates.YearLocator())
    eixo.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    eixo.grid(axis="y", color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    eixo.legend(frameon=False, loc="upper left", ncol=2)
    fig.savefig(raiz / "docs/grafico-divida.png", dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
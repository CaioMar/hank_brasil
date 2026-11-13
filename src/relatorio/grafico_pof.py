"""Gera o gráfico descritivo da composição de consumo por faixa da POF."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl


def main():
    raiz = Path(__file__).resolve().parents[2]
    dados = pl.read_csv(raiz / "docs/pof-2017-2018.csv").sort("codigo_classe")
    posicoes = np.arange(dados.height)
    figura, eixo = plt.subplots(figsize=(11, 5), layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    eixo.barh(posicoes - 0.19, dados["alimentacao_pct_consumo"].to_list(), 0.38, color="#a64431", label="Alimentação")
    eixo.barh(posicoes + 0.19, dados["habitacao_pct_consumo"].to_list(), 0.38, color="#14675a", label="Habitação")
    eixo.set_yticks(posicoes, dados["classe"].to_list())
    eixo.invert_yaxis()
    eixo.set_xlabel("Parcela da despesa de consumo (%)")
    eixo.set_xlim(0, 50)
    eixo.grid(axis="x", color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    eixo.legend(frameon=False, loc="lower right")
    figura.savefig(raiz / "docs/grafico-pof.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)


if __name__ == "__main__":
    main()
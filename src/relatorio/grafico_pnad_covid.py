"""Gera gráfico descritivo dos auxílios na PNAD COVID-19."""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def main():
    raiz = Path(__file__).resolve().parents[2]
    dados = pl.read_csv(raiz / "docs/pnad-covid-auxilios.csv").sort("mes")
    figura, eixo = plt.subplots(figsize=(11, 4), layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    eixo.plot(["Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov"], dados["domicilios_pct_auxilio"].to_list(),
              color="#14675a", marker="o", linewidth=2.5)
    eixo.set_ylim(0, 50)
    eixo.set_ylabel("Domicílios com auxílio (%)")
    eixo.grid(axis="y", color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    figura.savefig(raiz / "docs/grafico-pnad-covid.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)


if __name__ == "__main__":
    main()
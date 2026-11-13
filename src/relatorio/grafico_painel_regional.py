"""Resume a dispersão estadual das vendas, normalizadas a fevereiro de 2020."""

from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import polars as pl


def calcular_resumo(painel):
    base = (painel.filter(pl.col("mes") == "2020-02")
            .select("uf", pl.col("indice_volume").alias("indice_fev2020")))
    if base.height != 27 or base["uf"].n_unique() != 27 or base.filter(pl.col("indice_fev2020") <= 0).height:
        raise ValueError("Referência de fevereiro de 2020 incompleta ou inválida.")
    valores = (painel.join(base, on="uf", how="inner", validate="m:1")
               .with_columns((100 * pl.col("indice_volume") / pl.col("indice_fev2020")).alias("indice_rebaseado")))
    resumo = (valores.group_by("mes").agg(
        pl.len().alias("unidades"),
        pl.col("indice_rebaseado").quantile(0.25, interpolation="linear").alias("primeiro_quartil"),
        pl.col("indice_rebaseado").median().alias("mediana"),
        pl.col("indice_rebaseado").quantile(0.75, interpolation="linear").alias("terceiro_quartil"),
    ).sort("mes"))
    if resumo.height != 23 or resumo.filter(pl.col("unidades") != 27).height:
        raise ValueError("Painel estadual incompleto ou com duplicatas.")
    return resumo


def main():
    raiz = Path(__file__).resolve().parents[2]
    resumo = calcular_resumo(pl.read_csv(raiz / "docs/painel-regional-2019-2020.csv"))
    resumo.write_csv(raiz / "docs/resumo-comercio-estadual.csv")
    datas = [date.fromisoformat(mes + "-01") for mes in resumo["mes"].to_list()]
    figura, eixo = plt.subplots(figsize=(11, 4), layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    eixo.fill_between(datas, resumo["primeiro_quartil"].to_list(), resumo["terceiro_quartil"].to_list(),
                      color="#b9d1c2", label="Metade central das UFs")
    eixo.plot(datas, resumo["mediana"].to_list(), color="#14675a", linewidth=2.5, label="Mediana das UFs")
    eixo.axhline(100, color="#a64431", linewidth=1)
    eixo.set_ylabel("Vendas reais\n(fevereiro de 2020 = 100)")
    eixo.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    eixo.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    eixo.grid(axis="y", color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    eixo.legend(frameon=False, loc="lower left", ncol=2)
    figura.savefig(raiz / "docs/grafico-comercio-estadual.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)
    print(resumo.filter(pl.col("mes").is_in(["2020-02", "2020-04", "2020-05", "2020-11"])))


if __name__ == "__main__":
    main()
"""Diagnóstico exploratório: exposição observada em 2020 e tendência do varejo em 2019."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl


RAIZ = Path(__file__).resolve().parents[2]
MESES_2019 = [f"2019-{mes:02d}" for mes in range(1, 13)]


def calcular_diagnostico(painel):
    anterior = painel.filter(pl.col("mes").is_in(MESES_2019)).sort("uf", "mes")
    exposicao = (painel.filter(pl.col("mes") == "2020-05")
                 .select("uf", "estado", "domicilios_pct_auxilio"))
    if exposicao.height != 27 or exposicao["uf"].n_unique() != 27 or exposicao["domicilios_pct_auxilio"].null_count():
        raise ValueError("Exposição de maio incompleta ou duplicada.")
    valores_exposicao = exposicao["domicilios_pct_auxilio"].to_numpy()
    if not np.all(np.isfinite(valores_exposicao) & (valores_exposicao >= 0) & (valores_exposicao <= 100)):
        raise ValueError("Exposição de maio inválida.")
    registros = []
    for (uf,), estado in anterior.group_by("uf", maintain_order=True):
        if estado["mes"].to_list() != MESES_2019:
            raise ValueError("Série anterior incompleta ou duplicada.")
        valores = estado["indice_volume"].to_numpy()
        if not np.all(np.isfinite(valores) & (valores > 0)):
            raise ValueError("Índice anterior inválido.")
        inclinacao = np.polyfit(np.arange(12), np.log(valores), 1)[0]
        registros.append({"uf": uf, "tendencia_2019_pct_mes": float(100 * np.expm1(inclinacao))})
    tendencias = pl.DataFrame(registros)
    dados = tendencias.join(exposicao, on="uf", how="inner", validate="1:1").sort("uf")
    if dados.height != 27:
        raise ValueError("Amostra de estados incompleta.")
    return dados


def main():
    painel = pl.read_csv(RAIZ / "docs/painel-regional-2019-2020.csv")
    dados = calcular_diagnostico(painel)
    dados.write_csv(RAIZ / "docs/diagnostico-tendencias.csv")
    exposicao = dados["domicilios_pct_auxilio"].to_numpy()
    tendencia = dados["tendencia_2019_pct_mes"].to_numpy()
    correlacao = np.corrcoef(exposicao, tendencia)[0, 1]
    figura, eixo = plt.subplots(figsize=(8, 5), layout="constrained")
    figura.patch.set_facecolor("#f5f7f4")
    eixo.set_facecolor("#f5f7f4")
    eixo.scatter(exposicao, tendencia, color="#14675a", s=48, alpha=0.8)
    eixo.axhline(0, color="#a64431", linewidth=1)
    eixo.set_xlabel("Domicílios que relataram auxílio em maio de 2020 (%)")
    eixo.set_ylabel("Tendência mensal de vendas em 2019 (%)")
    eixo.grid(color="#d5ded8", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors="#50645d", length=0, pad=8)
    for borda in eixo.spines.values():
        borda.set_visible(False)
    figura.savefig(RAIZ / "docs/grafico-diagnostico-previo.png", dpi=160, facecolor=figura.get_facecolor())
    plt.close(figura)
    print(f"27 UFs; correlação de Pearson = {correlacao:.4f}")
    print(dados.select(pl.col("domicilios_pct_auxilio").min().alias("aux_min"),
                       pl.col("domicilios_pct_auxilio").max().alias("aux_max"),
                       pl.col("tendencia_2019_pct_mes").min().alias("tend_min"),
                       pl.col("tendencia_2019_pct_mes").max().alias("tend_max")))


if __name__ == "__main__":
    main()
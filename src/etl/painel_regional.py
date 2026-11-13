"""Combina indicadores públicos estaduais, sem estimar efeitos causais."""

from urllib.request import urlopen

import polars as pl

from src.etl.pnad_covid import RAIZ, URL, ler_responsaveis


def resumir_estados(dados, mes):
    agrupados = (dados.group_by("UF")
                 .agg(
                     pl.len().alias("domicilios_amostra"),
                     pl.col("D0051").is_null().sum().alias("respostas_ausentes"),
                     pl.when(pl.col("D0051").is_in(["1", "2"]))
                     .then(pl.col("V1032")).otherwise(0.0).sum().alias("peso_resposta_conhecida"),
                     pl.when(pl.col("D0051") == "1")
                     .then(pl.col("V1032")).otherwise(0.0).sum().alias("peso_auxilio"),
                 )
                 .rename({"UF": "uf"})
                 .with_columns(pl.lit(f"2020-{mes:02d}").alias("mes")))
    if agrupados.filter(pl.col("peso_resposta_conhecida") <= 0).height:
        raise ValueError("Estado sem respostas conhecidas sobre auxílios.")
    return agrupados.with_columns(
        (100 * pl.col("peso_auxilio") / pl.col("peso_resposta_conhecida")).alias("domicilios_pct_auxilio")
    )


def main():
    comercio = pl.read_csv(RAIZ / "docs/comercio-estadual-2019-2020.csv")
    resultados = []
    for mes in range(5, 12):
        with urlopen(URL.format(mes=mes), timeout=90) as resposta:
            dados = ler_responsaveis(resposta.read(), mes)
        estados = resumir_estados(dados, mes)
        if estados.height != 27:
            raise ValueError("Microdados sem todas as unidades da federação.")
        resultados.append(estados)
    auxilios = pl.concat(resultados)
    painel = comercio.join(auxilios, on=["uf", "mes"], how="left", validate="1:1").sort("uf", "mes")
    if (painel.height != 27 * 23 or painel.filter(pl.col("mes") >= "2020-05")["domicilios_pct_auxilio"].null_count()
            or painel.filter(pl.col("mes") < "2020-05")["domicilios_pct_auxilio"].null_count() != 27 * 16):
        raise ValueError("A junção regional contém períodos ou unidades da federação inesperados.")
    painel.write_csv(RAIZ / "docs/painel-regional-2019-2020.csv")
    print(f"{painel.height} observações; {auxilios.height} com auxílios observados em 2020")
    print(painel.filter(pl.col("mes") == "2020-05").select("estado", "mes", "indice_volume", "domicilios_pct_auxilio").head(3))


if __name__ == "__main__":
    main()
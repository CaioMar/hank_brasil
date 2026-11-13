"""Obtém indicadores agregados da POF 2017-2018 publicados pelo IBGE."""

import gzip
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import polars as pl


URL = "https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos/2018/variaveis/{variavel}"
RAIZ = Path(__file__).resolve().parents[2]
CLASSES = {str(codigo) for codigo in range(47558, 47565)}


def consultar(tabela, variavel, classificacao, categorias):
    parametros = urlencode({
        "localidades": "N1[all]",
        "classificacao": f"339[all]|{classificacao}[{','.join(categorias)}]",
    })
    with urlopen(f"{URL.format(tabela=tabela, variavel=variavel)}?{parametros}", timeout=40) as resposta:
        conteudo = resposta.read()
    if conteudo.startswith(b"\x1f\x8b"):
        conteudo = gzip.decompress(conteudo)
    dados = json.loads(conteudo)
    registros = []
    for resultado in dados[0]["resultados"]:
        classificacoes = {item["id"]: item["categoria"] for item in resultado["classificacoes"]}
        codigo_classe, classe = next(iter(classificacoes["339"].items()))
        if codigo_classe not in CLASSES:
            continue
        codigo_categoria = next(iter(classificacoes[str(classificacao)]))
        series = resultado["series"]
        if len(series) != 1 or series[0]["localidade"]["id"] != "1":
            raise ValueError("Localidade inesperada na resposta do IBGE.")
        try:
            valor = float(series[0]["serie"]["2018"])
        except (KeyError, TypeError, ValueError) as erro:
            raise ValueError("Valor ausente ou inválido na resposta do IBGE.") from erro
        if not math.isfinite(valor) or valor < 0:
            raise ValueError("Valor não finito ou negativo na resposta do IBGE.")
        registros.append({"codigo_classe": codigo_classe, "classe": classe, "indicador": codigo_categoria, "valor": valor})
    dados = pl.DataFrame(registros)
    if (dados.height != len(CLASSES) * len(categorias)
            or set(dados["codigo_classe"]) != CLASSES or set(dados["indicador"]) != set(categorias)
            or dados.select("codigo_classe", "indicador").is_duplicated().any()):
        raise ValueError("Categorias de renda ou indicadores incompletos na resposta do IBGE.")
    return dados.pivot(on="indicador", index=["codigo_classe", "classe"], values="valor")


def obter_indicadores():
    despesas = consultar(6715, 1201, 12190, ["103538", "103539", "103540"]).rename({
        "103538": "consumo", "103539": "alimentacao", "103540": "habitacao",
    })
    rendimentos = consultar(6974, 388, 4908, ["8049", "103423"]).rename({
        "8049": "rendimento_e_variacao_patrimonial", "103423": "rendimento_total",
    })
    dados = despesas.join(rendimentos, on=["codigo_classe", "classe"], how="inner").sort("codigo_classe")
    if (dados.height != len(CLASSES) or dados.null_count().row(0) != (0,) * dados.width
            or dados.filter(pl.col("consumo") <= 0).height):
        raise ValueError("As faixas das tabelas de despesa e rendimento não coincidem.")
    return dados.with_columns(
        (100 * pl.col("alimentacao") / pl.col("consumo")).alias("alimentacao_pct_consumo"),
        (100 * pl.col("habitacao") / pl.col("consumo")).alias("habitacao_pct_consumo"),
    )


def main():
    dados = obter_indicadores()
    dados.write_csv(RAIZ / "docs/pof-2017-2018.csv")
    print(dados)


if __name__ == "__main__":
    main()
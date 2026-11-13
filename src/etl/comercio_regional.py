"""Obtém vendas reais estaduais da Pesquisa Mensal de Comércio do IBGE."""

import gzip
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import polars as pl


RAIZ = Path(__file__).resolve().parents[2]
URL = "https://servicodados.ibge.gov.br/api/v3/agregados/3416/periodos/201901-202011/variaveis/564"
MESES = [f"{ano}{mes:02d}" for ano in (2019, 2020) for mes in range(1, 13) if (ano, mes) <= (2020, 11)]


def obter_comercio():
    parametros = urlencode({"localidades": "N3[all]", "classificacao": "11046[40312]"})
    with urlopen(f"{URL}?{parametros}", timeout=60) as resposta:
        conteudo = resposta.read()
    if conteudo.startswith(b"\x1f\x8b"):
        conteudo = gzip.decompress(conteudo)
    resultados = json.loads(conteudo)
    registros = []
    for localidade in resultados[0]["resultados"][0]["series"]:
        regiao = localidade["localidade"]
        if regiao["nivel"]["id"] != "N3" or set(localidade["serie"]) != set(MESES):
            raise ValueError("Localidade ou meses inesperados na série de comércio.")
        for periodo, texto in localidade["serie"].items():
            try:
                valor = float(texto)
            except (TypeError, ValueError) as erro:
                raise ValueError("Índice de comércio ausente ou inválido.") from erro
            if not math.isfinite(valor) or valor <= 0:
                raise ValueError("Índice de comércio não finito ou não positivo.")
            registros.append({"uf": int(regiao["id"]), "estado": regiao["nome"],
                              "mes": f"{periodo[:4]}-{periodo[4:]}", "indice_volume": valor})
    dados = pl.DataFrame(registros).sort("uf", "mes")
    if dados.height != 27 * len(MESES) or dados["uf"].n_unique() != 27 or dados.select("uf", "mes").is_duplicated().any():
        raise ValueError("Dados estaduais incompletos ou duplicados.")
    return dados


def main():
    dados = obter_comercio()
    dados.write_csv(RAIZ / "docs/comercio-estadual-2019-2020.csv")
    print(f"{dados['uf'].n_unique()} unidades da federação, {dados['mes'].n_unique()} meses, {dados.height} observações")
    print(dados.head(3))


if __name__ == "__main__":
    main()
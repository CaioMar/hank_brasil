"""Resume auxílios relacionados à pandemia na PNAD COVID-19 do IBGE."""

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import polars as pl


RAIZ = Path(__file__).resolve().parents[2]
URL = "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_PNAD_COVID19/Microdados/Dados/PNAD_COVID_{mes:02d}2020.zip"
COLUNAS = ["Ano", "UF", "UPA", "V1008", "V1013", "A001A", "V1032", "D0051"]


def resumir_mes(arquivo_zip, mes):
    with ZipFile(BytesIO(arquivo_zip)) as arquivo:
        nomes = [nome for nome in arquivo.namelist() if nome.lower().endswith(".csv")]
        if len(nomes) != 1:
            raise ValueError("Esperado um arquivo CSV por mês da PNAD COVID-19.")
        with arquivo.open(nomes[0]) as csv:
            dados = pl.read_csv(csv, columns=COLUNAS, schema_overrides={
                "UPA": pl.String, "V1008": pl.String, "A001A": pl.String, "D0051": pl.String,
            })
    dados = dados.filter(pl.col("A001A") == "01")
    if dados.is_empty() or dados.filter((pl.col("Ano") != 2020) | (pl.col("V1013") != mes)).height:
        raise ValueError("Mês ou ano dos microdados não corresponde ao solicitado.")
    if dados.select(pl.struct("UF", "UPA", "V1008").is_duplicated().any()).item():
        raise ValueError("Há mais de um responsável por domicílio.")
    if dados.filter(pl.col("V1032").is_null() | ~pl.col("V1032").is_finite() | (pl.col("V1032") <= 0)).height:
        raise ValueError("Peso domiciliar ausente ou inválido.")
    if dados.filter(pl.col("D0051").is_not_null() & ~pl.col("D0051").is_in(["1", "2"])).height:
        raise ValueError("Resposta inesperada sobre auxílios emergenciais.")
    conhecidos = dados.filter(pl.col("D0051").is_in(["1", "2"]))
    peso_conhecido = conhecidos["V1032"].sum()
    if not peso_conhecido:
        raise ValueError("Nenhuma resposta conhecida sobre auxílios emergenciais.")
    peso_beneficiados = conhecidos.filter(pl.col("D0051") == "1")["V1032"].sum() or 0.0
    return {
        "mes": f"2020-{mes:02d}",
        "domicilios_amostra": dados.height,
        "respostas_ausentes": dados.height - conhecidos.height,
        "domicilios_estimados_resposta_conhecida": peso_conhecido,
        "domicilios_estimados_auxilio": peso_beneficiados,
        "domicilios_pct_auxilio": 100 * peso_beneficiados / peso_conhecido,
    }


def main():
    resultados = []
    for mes in range(5, 12):
        with urlopen(URL.format(mes=mes), timeout=90) as resposta:
            resultados.append(resumir_mes(resposta.read(), mes))
    dados = pl.DataFrame(resultados)
    dados.write_csv(RAIZ / "docs/pnad-covid-auxilios.csv")
    print(dados)


if __name__ == "__main__":
    main()
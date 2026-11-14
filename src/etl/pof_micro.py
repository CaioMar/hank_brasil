"""Resume registros públicos da POF por unidade de consumo, sem publicar microdados."""

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import polars as pl


RAIZ = Path(__file__).resolve().parents[2]
CHAVE = ["cod_upa", "num_dom", "num_uc"]
CODIGOS = ["5400101", "5400102"]


def ler_largura_fixa(arquivo, campos):
    dados = pl.read_csv(BytesIO(arquivo), has_header=False, new_columns=["linha"],
                        separator="\t", schema_overrides={"linha": pl.String})
    return dados.select([
        pl.col("linha").str.slice(inicio, largura).str.strip_chars().alias(nome)
        for nome, inicio, largura in campos
    ])


def resumir(moradores, rendimentos):
    moradores = moradores.with_columns(pl.col("peso_final").cast(pl.Float64, strict=True))
    if moradores.filter(
        pl.any_horizontal([pl.col(coluna).is_null() | (pl.col(coluna) == "") for coluna in CHAVE])
        | pl.col("peso_final").is_null() | ~pl.col("peso_final").is_finite()
        | (pl.col("peso_final") <= 0)
    ).height:
        raise ValueError("Chave ou peso de morador inválido.")
    unidades = moradores.group_by(CHAVE).agg(
        pl.col("peso_final").first(), pl.col("peso_final").n_unique().alias("pesos_distintos")
    )
    if unidades.filter(pl.col("pesos_distintos") != 1).height:
        raise ValueError("Pesos inconsistentes dentro da unidade de consumo.")
    beneficios = rendimentos.filter(pl.col("codigo").is_in(CODIGOS))
    if beneficios.filter(
        pl.any_horizontal([pl.col(coluna).is_null() | (pl.col(coluna) == "") for coluna in CHAVE])
    ).height:
        raise ValueError("Chave de rendimento inválida.")
    if beneficios.filter(
        (pl.col("quadro") != "54") | ~pl.col("imputado").is_in(["0", "1"])
        | ~pl.col("meses").is_in([str(mes) for mes in range(1, 13)])
        | pl.any_horizontal([pl.col(coluna).is_null() for coluna in ["quadro", "imputado", "meses"]])
    ).height:
        raise ValueError("Quadro, meses ou indicador de imputação inválido.")
    beneficiarias = beneficios.select(CHAVE).unique().with_columns(pl.lit(True).alias("registro"))
    if beneficiarias.join(unidades, on=CHAVE, how="anti").height:
        raise ValueError("Registro de benefício sem unidade de consumo correspondente.")
    unidos = unidades.join(beneficiarias, on=CHAVE, how="left", validate="1:1").with_columns(
        pl.col("registro").fill_null(False)
    )
    peso_total = unidos["peso_final"].sum()
    if not peso_total:
        raise ValueError("Amostra de unidades de consumo vazia.")
    peso_beneficio = unidos.filter(pl.col("registro"))["peso_final"].sum()
    return pl.DataFrame({
        "unidades_amostra": [unidos.height],
        "unidades_com_registro_amostra": [unidos.filter(pl.col("registro")).height],
        "unidades_estimadas": [peso_total],
        "unidades_com_registro_estimadas": [peso_beneficio],
        "percentual_com_registro": [100 * peso_beneficio / peso_total],
        "registros_beneficio": [beneficios.height],
        "registros_valor_imputado": [beneficios.filter(pl.col("imputado") == "1").height],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, required=True, help="ZIP oficial de microdados da POF")
    argumentos = parser.parse_args()
    with ZipFile(argumentos.arquivo) as arquivo:
        moradores = ler_largura_fixa(arquivo.read("MORADOR.txt"), [
            ("cod_upa", 7, 9), ("num_dom", 16, 2), ("num_uc", 18, 1), ("peso_final", 91, 14),
        ])
        rendimentos = ler_largura_fixa(arquivo.read("OUTROS_RENDIMENTOS.txt"), [
            ("cod_upa", 7, 9), ("num_dom", 16, 2), ("num_uc", 18, 1), ("codigo", 25, 7),
            ("quadro", 21, 2), ("meses", 54, 2), ("imputado", 88, 1),
        ])
    resultado = resumir(moradores, rendimentos)
    resultado.write_csv(RAIZ / "docs/pof-micro-beneficios.csv")
    print(resultado)


if __name__ == "__main__":
    main()
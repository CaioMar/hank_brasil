import gzip
from io import BytesIO
import json
import unittest
from unittest.mock import patch

import numpy as np
import polars as pl

from src.etl.comercio_regional import MESES, obter_comercio
from src.etl.painel_regional import resumir_estados
from src.relatorio.diagnostico_previo import calcular_diagnostico
from src.relatorio.grafico_painel_regional import calcular_resumo


def resposta_comercio():
    series = [{"localidade": {"id": str(uf), "nome": f"UF {uf}", "nivel": {"id": "N3"}},
               "serie": {mes: "100.0" for mes in MESES}} for uf in range(1, 28)]
    return [{"resultados": [{"series": series}]}]


class TestPainelRegional(unittest.TestCase):
    def test_comercio_aceita_gzip_e_exige_cobertura_completa(self):
        resposta = gzip.compress(json.dumps(resposta_comercio()).encode())
        with patch("src.etl.comercio_regional.urlopen", return_value=BytesIO(resposta)):
            dados = obter_comercio()
        self.assertEqual(dados.height, 27 * 23)
        self.assertEqual(dados["uf"].n_unique(), 27)

    def test_comercio_rejeita_mes_ausente(self):
        resposta = resposta_comercio()
        resposta[0]["resultados"][0]["series"][0]["serie"].pop("201901")
        with patch("src.etl.comercio_regional.urlopen", return_value=BytesIO(json.dumps(resposta).encode())):
            with self.assertRaisesRegex(ValueError, "meses inesperados"):
                obter_comercio()

    def test_exclui_resposta_ausente_do_denominador(self):
        dados = pl.DataFrame({"UF": [11, 11, 11, 12], "D0051": ["1", "2", None, "1"],
                              "V1032": [3.0, 1.0, 5.0, 2.0]})
        resultado = resumir_estados(dados, 5).sort("uf")
        self.assertEqual(resultado["domicilios_pct_auxilio"].to_list(), [75.0, 100.0])
        self.assertEqual(resultado["respostas_ausentes"].to_list(), [1, 0])

    def test_referencia_e_mediana_por_estado(self):
        dados = pl.DataFrame([
            {"uf": uf, "mes": f"{mes[:4]}-{mes[4:]}", "indice_volume": 50.0 if mes == "202004" else 100.0}
            for uf in range(1, 28) for mes in MESES
        ])
        resumo = calcular_resumo(dados)
        self.assertEqual(resumo.filter(pl.col("mes") == "2020-02")["mediana"].item(), 100.0)
        self.assertEqual(resumo.filter(pl.col("mes") == "2020-04")["mediana"].item(), 50.0)

    def test_tendencia_anterior_e_exposicao_posterior(self):
        dados = pl.DataFrame([
            {"uf": uf, "estado": f"UF {uf}", "mes": f"2019-{mes:02d}",
             "indice_volume": 100 * 1.01 ** (mes - 1), "domicilios_pct_auxilio": None}
            for uf in range(1, 28) for mes in range(1, 13)
        ] + [
            {"uf": uf, "estado": f"UF {uf}", "mes": "2020-05",
             "indice_volume": 100.0, "domicilios_pct_auxilio": float(uf)}
            for uf in range(1, 28)
        ], infer_schema_length=None)
        resultado = calcular_diagnostico(dados)
        self.assertEqual(resultado.height, 27)
        np.testing.assert_allclose(resultado["tendencia_2019_pct_mes"].to_numpy(), 1.0, atol=1e-10)
        self.assertEqual(resultado["domicilios_pct_auxilio"].to_list(), list(map(float, range(1, 28))))
        with self.assertRaisesRegex(ValueError, "Série anterior incompleta"):
            calcular_diagnostico(dados.filter(~((pl.col("uf") == 1) & (pl.col("mes") == "2019-01"))))
        with self.assertRaisesRegex(ValueError, "Exposição de maio inválida"):
            calcular_diagnostico(dados.with_columns(
                pl.when((pl.col("uf") == 1) & (pl.col("mes") == "2020-05"))
                .then(float("nan")).otherwise(pl.col("domicilios_pct_auxilio"))
                .alias("domicilios_pct_auxilio")
            ))


if __name__ == "__main__":
    unittest.main()
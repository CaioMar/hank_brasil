from datetime import date
from io import BytesIO
import unittest
from unittest.mock import patch

import openpyxl
import polars as pl

from src.relatorio.grafico_contas_publicas import obter_contas_tesouro, obter_dados


class TestContasPublicas(unittest.TestCase):
    def serie_mensal(self, codigo, inicio, fim):
        valores = {5793: 1.0, 5760: 6.0, 5727: 7.0, 432: 10.0}
        return pl.DataFrame({
            "data": [date(ano, mes, 1) for ano in range(2015, 2026) for mes in range(1, 13)],
            "valor": [valores[codigo]] * 132,
        })

    def test_seleciona_dezembro_e_valida_identidade(self):
        with patch("src.relatorio.grafico_contas_publicas.baixar_serie", side_effect=self.serie_mensal):
            dados = obter_dados()
        self.assertEqual(dados["ano"].to_list(), list(range(2015, 2026)))
        self.assertEqual(dados["nominal"].to_list(), [7.0] * 11)

    def test_rejeita_identidade_inconsistente(self):
        def serie_incorreta(codigo, inicio, fim):
            dados = self.serie_mensal(codigo, inicio, fim)
            return dados.with_columns((pl.col("valor") + 1).alias("valor")) if codigo == 5727 else dados

        with patch("src.relatorio.grafico_contas_publicas.baixar_serie", side_effect=serie_incorreta):
            with self.assertRaisesRegex(ValueError, "identidade fiscal"):
                obter_dados()

    def test_converte_contas_do_tesouro_em_percentual_do_pib(self):
        planilha = openpyxl.Workbook()
        aba = planilha.active
        aba.title = "2.1"
        aba.append(["Título"])
        aba.append(["Tabela"])
        aba.append(["R$ Milhões - Valores Correntes"])
        aba.append([])
        aba.append(["Discriminação", *range(2015, 2026)])
        aba.append(["3. RECEITA LÍQUIDA  (1-2)", *([100.0] * 11)])
        aba.append(["4. DESPESA TOTAL", *([120.0] * 11)])
        arquivo = BytesIO()
        planilha.save(arquivo)
        pib = pl.DataFrame({"data": [date(ano, 1, 1) for ano in range(2015, 2026)], "valor": [1_000_000_000.0] * 11})
        with patch("src.relatorio.grafico_contas_publicas.urlopen", return_value=BytesIO(arquivo.getvalue())), \
             patch("src.relatorio.grafico_contas_publicas.baixar_serie", return_value=pib):
            dados = obter_contas_tesouro()
        self.assertEqual(dados["receita_primaria_gc"].to_list(), [10.0] * 11)
        self.assertEqual(dados["despesa_primaria_gc"].to_list(), [12.0] * 11)


if __name__ == "__main__":
    unittest.main()
import unittest

import polars as pl

from src.etl.pof_micro import ler_largura_fixa, resumir


class TestPofMicro(unittest.TestCase):
    def test_leitura_largura_fixa(self):
        dados = ler_largura_fixa(b"  11 02\r\n  22 03\r\n", [("upa", 0, 4), ("dom", 4, 3)])
        self.assertEqual(dados.to_dicts(), [{"upa": "11", "dom": "02"}, {"upa": "22", "dom": "03"}])

    def test_unidade_ponderada_nao_duplica_moradores_ou_registros(self):
        moradores = pl.DataFrame({"cod_upa": ["1", "1", "2"], "num_dom": ["01"] * 3,
                                 "num_uc": ["1"] * 3, "peso_final": ["2", "2", "3"]})
        rendimentos = pl.DataFrame({"cod_upa": ["1", "1", "2"], "num_dom": ["01"] * 3,
                                    "num_uc": ["1"] * 3,
                                    "codigo": ["5400101", "5400102", "5400301"],
                                    "quadro": ["54"] * 3, "meses": ["12"] * 3,
                                    "imputado": ["0", "1", "0"]})
        resultado = resumir(moradores, rendimentos).row(0, named=True)
        self.assertEqual(resultado["unidades_amostra"], 2)
        self.assertEqual(resultado["unidades_com_registro_amostra"], 1)
        self.assertEqual(resultado["unidades_estimadas"], 5)
        self.assertEqual(resultado["percentual_com_registro"], 40)
        self.assertEqual(resultado["registros_beneficio"], 2)
        self.assertEqual(resultado["registros_valor_imputado"], 1)

    def test_rejeita_pesos_inconsistentes_e_chave_sem_morador(self):
        moradores = pl.DataFrame({"cod_upa": ["1", "1"], "num_dom": ["01", "01"],
                                 "num_uc": ["1", "1"], "peso_final": ["2", "3"]})
        rendimentos = pl.DataFrame({"cod_upa": ["2"], "num_dom": ["01"],
                                    "num_uc": ["1"], "codigo": ["5400102"],
                                    "quadro": ["54"], "meses": ["12"], "imputado": ["0"]})
        with self.assertRaisesRegex(ValueError, "Pesos inconsistentes"):
            resumir(moradores, rendimentos)
        with self.assertRaisesRegex(ValueError, "sem unidade"):
            resumir(moradores.head(1), rendimentos)


if __name__ == "__main__":
    unittest.main()
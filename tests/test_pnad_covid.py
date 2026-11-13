from io import BytesIO
import unittest
from zipfile import ZipFile

from src.etl.pnad_covid import resumir_mes


def arquivo_amostra(linhas):
    conteudo = "Ano,UF,UPA,V1008,V1013,A001A,V1032,D0051\n" + "\n".join(linhas) + "\n"
    arquivo = BytesIO()
    with ZipFile(arquivo, "w") as zipado:
        zipado.writestr("dados.csv", conteudo)
    return arquivo.getvalue()


class TestPnadCovid(unittest.TestCase):
    def test_peso_domiciliar_sem_duplicar_moradores(self):
        arquivo = arquivo_amostra([
            "2020,11,101,01,5,01,3.0,1",
            "2020,11,101,01,5,02,3.0,1",
            "2020,11,101,02,5,01,1.0,2",
            "2020,11,101,03,5,01,2.0,",
        ])
        resultado = resumir_mes(arquivo, 5)
        self.assertEqual(resultado["domicilios_amostra"], 3)
        self.assertEqual(resultado["respostas_ausentes"], 1)
        self.assertEqual(resultado["domicilios_estimados_resposta_conhecida"], 4.0)
        self.assertEqual(resultado["domicilios_estimados_auxilio"], 3.0)
        self.assertEqual(resultado["domicilios_pct_auxilio"], 75.0)

    def test_rejeita_responsaveis_duplicados(self):
        arquivo = arquivo_amostra(["2020,11,101,01,5,01,3.0,1", "2020,11,101,01,5,01,3.0,1"])
        with self.assertRaisesRegex(ValueError, "mais de um responsável"):
            resumir_mes(arquivo, 5)

    def test_rejeita_resposta_inesperada(self):
        arquivo = arquivo_amostra(["2020,11,101,01,5,01,3.0,9"])
        with self.assertRaisesRegex(ValueError, "Resposta inesperada"):
            resumir_mes(arquivo, 5)

    def test_rejeita_mes_incorreto(self):
        arquivo = arquivo_amostra(["2020,11,101,01,5,01,3.0,1"])
        with self.assertRaisesRegex(ValueError, "Mês ou ano"):
            resumir_mes(arquivo, 6)


if __name__ == "__main__":
    unittest.main()
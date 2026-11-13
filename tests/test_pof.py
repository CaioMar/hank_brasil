import gzip
from io import BytesIO
import json
import unittest
from unittest.mock import patch

from src.etl.pof import consultar, obter_indicadores


def resposta_ibge(classificacao, categorias, valor_invalido=False):
    resultados = []
    for codigo in range(47558, 47565):
        for categoria in categorias:
            valor = "NaN" if valor_invalido else {"103538": "100", "103539": "20", "103540": "40", "8049": "120", "103423": "110"}[categoria]
            resultados.append({
                "classificacoes": [
                    {"id": "339", "categoria": {str(codigo): f"Faixa {codigo}"}},
                    {"id": str(classificacao), "categoria": {categoria: "Indicador"}},
                ],
                "series": [{"localidade": {"id": "1"}, "serie": {"2018": valor}}],
            })
    return json.dumps([{"resultados": resultados}]).encode()


class TestPof(unittest.TestCase):
    def test_leitura_json_e_gzip_e_calculo_de_parcelas(self):
        despesas = resposta_ibge(12190, ["103538", "103539", "103540"])
        rendimentos = resposta_ibge(4908, ["8049", "103423"])
        with patch("src.etl.pof.urlopen", side_effect=[BytesIO(despesas), BytesIO(gzip.compress(rendimentos))]):
            dados = obter_indicadores()
        self.assertEqual(dados.height, 7)
        self.assertEqual(dados["alimentacao_pct_consumo"].to_list(), [20.0] * 7)
        self.assertEqual(dados["habitacao_pct_consumo"].to_list(), [40.0] * 7)

    def test_rejeita_valor_nao_finito(self):
        dados = resposta_ibge(12190, ["103538"], valor_invalido=True)
        with patch("src.etl.pof.urlopen", return_value=BytesIO(dados)):
            with self.assertRaisesRegex(ValueError, "não finito"):
                consultar(6715, 1201, 12190, ["103538"])

    def test_rejeita_categoria_incompleta(self):
        dados = resposta_ibge(12190, ["103538"])
        with patch("src.etl.pof.urlopen", return_value=BytesIO(dados)):
            with self.assertRaisesRegex(ValueError, "incompletos"):
                consultar(6715, 1201, 12190, ["103538", "103539"])


if __name__ == "__main__":
    unittest.main()
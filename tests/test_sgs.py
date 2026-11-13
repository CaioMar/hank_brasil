import io
import json
import unittest
from datetime import date
from unittest.mock import patch

import jax
import jax.numpy as jnp
import polars as pl

from src.etl.sgs import baixar_serie, calibrar_inicial, preparar_historico, simular_historico
from simulacao_hank_brasil import criar_simulador_jax


class Resposta(io.BytesIO):
    pass


class TesteSGS(unittest.TestCase):
    def dados(self):
        meses = [date(2023, mes, 1) for mes in range(2, 13)] + [date(2024, mes, 1) for mes in range(1, 4)]
        return pl.DataFrame({
            "mes": meses,
            "selic": [10.0] * len(meses),
            "ipca": [1.0] * len(meses),
            "divida_pib": [80.0] * len(meses),
            "reservas": [388000.0] * len(meses),
            "cambio": [5.0] * len(meses),
        })

    def test_unidades_e_janela_inicial(self):
        dados = preparar_historico(self.dados(), date(2024, 1, 1), date(2024, 3, 1))
        parametros = calibrar_inicial(dados)
        self.assertAlmostEqual(parametros["inflacao_inicial"], 1.01 ** 12 - 1)
        self.assertEqual(parametros["selic_inicial"], 0.1)
        self.assertEqual(parametros["divida_inicial"], 80.0)
        self.assertEqual(parametros["reservas_iniciais"], 388.0)
        self.assertEqual(parametros["cambio_inicial"], 5.0)

    def test_lacunas_e_duplicatas_sao_rejeitadas(self):
        dados = self.dados()
        with self.assertRaisesRegex(ValueError, "IPCA ausente"):
            preparar_historico(dados.filter(pl.col("mes") != date(2023, 7, 1)), date(2024, 1, 1), date(2024, 3, 1))
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            preparar_historico(pl.concat([dados, dados.tail(1)]), date(2024, 1, 1), date(2024, 3, 1))

    def test_download_divide_anos_e_interpreta_datas(self):
        respostas = [
            Resposta(json.dumps([{"data": "31/12/2023", "valor": "10.5"}]).encode()),
            Resposta(json.dumps([{"data": "01/01/2024", "valor": "10.0"}]).encode()),
        ]
        with patch("src.etl.sgs.urlopen", side_effect=respostas) as requisicoes:
            dados = baixar_serie(432, date(2023, 12, 1), date(2024, 1, 31))
        self.assertEqual(requisicoes.call_count, 2)
        self.assertEqual(dados["data"].to_list(), [date(2023, 12, 31), date(2024, 1, 1)])
        self.assertEqual(dados["valor"].to_list(), [10.5, 10.0])

    def test_simulacao_comeca_no_mes_seguinte_e_e_finita(self):
        dados = preparar_historico(self.dados(), date(2024, 1, 1), date(2024, 3, 1))
        resultado = simular_historico(dados, calibrar_inicial(dados), n_agentes=100)
        self.assertEqual(resultado["mes"].to_list(), [date(2024, 2, 1), date(2024, 3, 1)])
        self.assertTrue(bool(jnp.isfinite(jnp.asarray(resultado["divida_pib_simulada"].to_numpy())).all()))

    def test_transferencias_nao_dependem_do_numero_de_agentes_e_sao_diferenciaveis(self):
        def simular_quantidade(quantidade):
            decis = jnp.repeat(jnp.arange(1, 11), quantidade // 10)
            renda = jnp.full((quantidade,), 100.0 / quantidade)
            riqueza = jnp.full((quantidade,), 82.9 / quantidade)
            pmc = jnp.where(decis <= 5, 0.9, 0.3)
            simular = criar_simulador_jax(decis, renda, pmc, riqueza)
            zeros = jnp.zeros(1)
            return lambda gasto: simular(jnp.array([0.1375]), jnp.array([gasto]), zeros, zeros, 0.0)[0][0]

        pequeno = simular_quantidade(10)
        grande = simular_quantidade(1000)
        self.assertAlmostEqual(float(pequeno(0.5)), float(grande(0.5)), places=3)
        gradiente = jax.grad(grande)(0.5)
        self.assertTrue(bool(jnp.isfinite(gradiente)))
        self.assertGreater(float(gradiente), 0.0)


if __name__ == "__main__":
    unittest.main()
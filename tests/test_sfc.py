import unittest

import jax
import jax.numpy as jnp
import numpy as np
import polars as pl
from datetime import date

from src.models.sfc import criar_simulador_sfc
from src.relatorio.experimento_sfc import executar


class TesteSFC(unittest.TestCase):
    def criar(self, gasto_privado_autonomo=0.0):
        decis = jnp.repeat(jnp.arange(1, 11), 10)
        renda = jnp.full((100,), 1.0)
        riqueza = jnp.full((100,), 0.8)
        pmc = jnp.where(decis <= 5, 0.9, 0.2)
        return criar_simulador_sfc(renda, pmc, riqueza, decis, 80.0, 0.12, gasto_privado_autonomo=gasto_privado_autonomo)

    def test_fluxos_e_estoques_fecham_com_choques(self):
        simular = self.criar(gasto_privado_autonomo=10.0)
        selic = jnp.array([0.12, 0.08, 0.1, 0.15])
        transferencias = jnp.array([0.0, 1.0, -0.5, 2.0])
        impostos = jnp.array([0.0, 0.1, 0.05, 0.2])
        isencoes = jnp.array([0.0, 0.01, 0.0, 0.02])
        inflacao = jnp.array([0.03, 0.04, 0.05, 0.02])
        resultado = simular(selic, transferencias, impostos, isencoes, inflacao)
        np.testing.assert_allclose(resultado["pib_nominal"], resultado["renda_producao"], rtol=2e-6)
        np.testing.assert_allclose(resultado["juros_publicos"], resultado["juros_familias"], rtol=2e-6)
        np.testing.assert_allclose(resultado["ativos"] - resultado["ativos_anteriores"], resultado["poupanca"] / 12, atol=5e-5)
        np.testing.assert_allclose(resultado["divida"] - resultado["divida_anterior"], (resultado["compras_publicas"] + resultado["transferencias"] + resultado["juros_publicos"] - resultado["tributos"]) / 12, atol=5e-5)
        np.testing.assert_allclose(resultado["ativos"], resultado["divida"], atol=5e-5)

    def test_gradiente_e_finito(self):
        simular = self.criar()
        zeros = jnp.zeros(2)
        def pib(transferencia):
            return simular(jnp.full(2, 0.12), jnp.full(2, transferencia), zeros, zeros, zeros)["pib_real"][-1]
        self.assertTrue(bool(jnp.isfinite(jax.grad(pib)(0.5))))

    def test_inicializacao_inconsistente_nao_e_escondida(self):
        decis = jnp.repeat(jnp.arange(1, 11), 10)
        simulador = criar_simulador_sfc(jnp.ones(100), jnp.full(100, 0.5), jnp.full(100, 0.7), decis, 80.0, 0.12)
        zeros = jnp.zeros(1)
        resultado = simulador(jnp.full(1, 0.12), zeros, zeros, zeros, zeros)
        self.assertAlmostEqual(float(resultado["residual_ativos_divida"][0]), -10.0 * (1.0 + 0.12 / 12.0), places=3)

    def test_ativos_negativos_nao_sao_cortados(self):
        decis = jnp.repeat(jnp.arange(1, 11), 10)
        ativos = jnp.full((100,), 0.9).at[0].set(-9.1)
        simulador = criar_simulador_sfc(jnp.ones(100), jnp.full(100, 0.5), ativos, decis, 80.0, 0.12)
        zeros = jnp.zeros(1)
        resultado = simulador(jnp.full(1, 0.12), zeros, zeros, zeros, zeros)
        self.assertLess(float(resultado["ativos_minimos"][0]), 0.0)
        self.assertGreater(float(resultado["fracao_ativos_negativos"][0]), 0.0)
        self.assertAlmostEqual(float(resultado["residual_ativos_divida"][0]), 0.0, places=3)

    def test_experimento_preserva_observado_e_ipca_mensal(self):
        historico = pl.DataFrame({
            "mes": [date(2024, 1, 1), date(2024, 2, 1)],
            "selic": [10.0, 11.0], "ipca": [0.5, 1.0], "ipca_12m": [5.0, 5.2],
            "divida_pib": [80.0, 81.0], "reservas": [388000.0, 388000.0], "cambio": [5.0, 5.1],
        })
        resultado = executar(historico, agentes=100)
        self.assertEqual(resultado["divida_pib"][0], 81.0)
        self.assertIn("sfc_divida_pib", resultado.columns)
        self.assertAlmostEqual(resultado["sfc_precos"][0], 1.01, places=5)
        ancorado = executar(historico.with_columns(pl.lit(0.0).alias("ipca")), agentes=100, ancorar_pib=True)
        self.assertAlmostEqual(ancorado["sfc_pib_real"][0], 100.0, delta=0.001)
        self.assertAlmostEqual(ancorado["sfc_residual_ativos_divida"][0], 0.0, delta=0.0001)


if __name__ == "__main__":
    unittest.main()
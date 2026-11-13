import io
import json
import unittest
from datetime import date
from unittest.mock import patch

import jax
import jax.numpy as jnp
import polars as pl

from src.etl.sgs import baixar_serie, calibrar_inicial, preparar_historico, simular_historico
from src.relatorio.diagnostico import calcular_diagnostico, gerar_relatorio
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

    def test_auditoria_expoe_ajustes_e_conserva_trajetoria(self):
        dados = preparar_historico(self.dados(), date(2024, 1, 1), date(2024, 3, 1))
        parametros = calibrar_inicial(dados)
        normal = simular_historico(dados, parametros, n_agentes=100)
        auditado = simular_historico(dados, parametros, n_agentes=100, auditoria=True)
        for comum, linha in zip(normal["divida_pib_simulada"], auditado.iter_rows(named=True)):
            self.assertAlmostEqual(comum, linha["divida_pib_simulada"], places=5)
            divida = linha["divida_anterior"] + (linha["juros_nominais_anualizados"] - linha["primario_nominal_anualizado"]) / 12
            self.assertAlmostEqual(linha["divida_nova"], divida, places=4)
            riqueza = (linha["riqueza_anterior"] + linha["poupanca_mensal"]
                       + linha["ajuste_piso_riqueza"] + linha["ajuste_normalizacao_riqueza"])
            self.assertAlmostEqual(linha["riqueza_nova"], riqueza, places=4)

        diagnostico = calcular_diagnostico(auditado)
        componentes = diagnostico.select(
            pl.sum("contribuicao_juros_pp"), pl.sum("contribuicao_primario_pp"),
            pl.sum("contribuicao_pib_nominal_pp"),
        ).row(0)
        variacao = diagnostico["divida_pib_simulada"][-1] - parametros["divida_inicial"]
        self.assertAlmostEqual(sum(componentes), variacao, places=4)
        relatorio = gerar_relatorio(diagnostico, parametros, 100)
        self.assertIn("não é uma previsão em tempo real", relatorio)
        self.assertIn("não prova consistência fluxo-estoque", relatorio)
        self.assertIn("--dados outra-janela", gerar_relatorio(diagnostico, parametros, 100, "outra-janela"))

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
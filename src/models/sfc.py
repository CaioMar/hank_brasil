"""Protótipo SFC de economia fechada, com fluxos anualizados e passos mensais."""

import jax
import jax.numpy as jnp


def criar_simulador_sfc(renda_base, pmc, ativos_iniciais, decil, divida_inicial, selic_inicial,
                        aliquota_base=0.325, gasto_compras=32.9, propensao_riqueza=0.032,
                        gasto_privado_autonomo=0.0):
    peso_renda = renda_base / jnp.sum(renda_base)
    peso_base = (decil <= 5).astype(jnp.float32)
    peso_base = peso_base / jnp.sum(peso_base)
    topo = (decil == 10).astype(jnp.float32)
    renda_inicial = (1.0 - aliquota_base) * renda_base + selic_inicial * ativos_iniciais

    @jax.jit
    def simular(selic, transferencias, aliquota_topo, revisao_isencoes, inflacao):
        def passo(estado, entradas):
            ativos, divida, renda_disponivel_ant, precos, juros_legados = estado
            selic_t, transferencias_t, imposto_topo_t, isencoes_t, inflacao_t = entradas
            precos_novos = precos * (1.0 + inflacao_t / 12.0)
            juros_legados_novos = juros_legados + (selic_t - juros_legados) / 36.0
            juros_efetivos = 0.55 * selic_t + 0.45 * juros_legados_novos

            consumo_individual = pmc * jnp.maximum(renda_disponivel_ant, 0.0) + propensao_riqueza * jnp.maximum(ativos, 0.0)
            consumo = jnp.sum(consumo_individual)
            compras_publicas = gasto_compras * precos_novos
            gasto_privado = gasto_privado_autonomo * precos_novos
            pib_nominal = consumo + gasto_privado + compras_publicas
            renda_producao = peso_renda * pib_nominal
            juros_familias = juros_efetivos * ativos
            transferencias_familias = transferencias_t * precos_novos * peso_base
            tributos_base = (aliquota_base + isencoes_t) * renda_producao
            tributos_topo = imposto_topo_t * jnp.maximum(juros_familias, 0.0) * topo
            tributos = tributos_base + tributos_topo
            renda_disponivel = renda_producao + juros_familias + transferencias_familias - tributos
            poupanca = renda_disponivel - consumo_individual - peso_renda * gasto_privado

            ativos_novos = ativos + poupanca / 12.0
            receita_publica = jnp.sum(tributos)
            juros_publicos = juros_efetivos * divida
            gasto_publico = compras_publicas + jnp.sum(transferencias_familias)
            divida_nova = divida + (gasto_publico + juros_publicos - receita_publica) / 12.0

            metricas = {
                "pib_nominal": pib_nominal,
                "pib_real": pib_nominal / precos_novos,
                "consumo": consumo,
                "gasto_privado_autonomo": gasto_privado,
                "compras_publicas": compras_publicas,
                "renda_producao": jnp.sum(renda_producao),
                "transferencias": jnp.sum(transferencias_familias),
                "tributos": receita_publica,
                "juros_publicos": juros_publicos,
                "juros_familias": jnp.sum(juros_familias),
                "poupanca": jnp.sum(poupanca),
                "divida_anterior": divida,
                "divida": divida_nova,
                "ativos_anteriores": jnp.sum(ativos),
                "ativos": jnp.sum(ativos_novos),
                "ativos_minimos": jnp.min(ativos_novos),
                "fracao_ativos_negativos": jnp.mean((ativos_novos < 0).astype(jnp.float32)),
                "residual_ativos_divida": jnp.sum(ativos_novos) - divida_nova,
                "residual_juros": jnp.sum(juros_familias) - juros_publicos,
                "divida_pib": 100.0 * divida_nova / pib_nominal,
                "precos": precos_novos,
            }
            return (ativos_novos, divida_nova, renda_disponivel, precos_novos, juros_legados_novos), metricas

        inicial = (ativos_iniciais, jnp.asarray(divida_inicial), renda_inicial, jnp.asarray(1.0), jnp.asarray(selic_inicial))
        _, historico = jax.lax.scan(passo, inicial, (selic, transferencias, aliquota_topo, revisao_isencoes, inflacao))
        return historico

    return simular
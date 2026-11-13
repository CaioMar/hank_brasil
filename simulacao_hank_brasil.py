import time
import numpy as np
import polars as pl
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt

# ==============================================================================
# 1. CALIBRAÇÃO DE AGENTES HETEROGÊNEOS VIA POLARS (PERFIL POF / IBGE)
# ==============================================================================
def gerar_populacao_agentes(n_agentes: int = 1_000_000, seed: int = 42, divida_inicial: float = 82.9):
    """
    Constrói uma população sintética de 1 milhão de agentes calibrada pelos
    10 decis de renda da POF/IBGE (participação na renda, PMC e riqueza financeira).
    """
    rng = np.random.default_rng(seed)

    tabela_decis = pl.DataFrame({
        "decil": list(range(1, 11)),
        "fatia_renda":   [0.012, 0.023, 0.034, 0.045, 0.058, 0.073, 0.092, 0.120, 0.168, 0.375],
        "pmc_media":     [0.940, 0.910, 0.880, 0.840, 0.790, 0.730, 0.660, 0.560, 0.420, 0.160],
        "fatia_riqueza": [0.001, 0.002, 0.004, 0.007, 0.012, 0.020, 0.034, 0.060, 0.130, 0.730],
    })

    print("=== Perfil Calibrado dos Decis (POF/IBGE) ===")
    print(tabela_decis)

    decis_agentes = np.repeat(np.arange(1, 11), n_agentes // 10)
    df_agentes = pl.DataFrame({"decil": decis_agentes}).join(
        tabela_decis, on="decil", how="left"
    )

    ruido_renda = rng.lognormal(mean=0.0, sigma=0.25, size=n_agentes)
    ruido_pmc = rng.normal(loc=0.0, scale=0.02, size=n_agentes)
    ruido_riq = rng.lognormal(mean=0.0, sigma=0.35, size=n_agentes)

    df_agentes = df_agentes.with_columns([
        (pl.col("fatia_renda") * pl.Series(ruido_renda)).alias("renda_bruta"),
        (pl.col("pmc_media") + pl.Series(ruido_pmc)).clip(0.05, 0.98).alias("pmc"),
        (pl.col("fatia_riqueza") * pl.Series(ruido_riq)).alias("riqueza_bruta"),
    ])

    PIB_INICIAL = 100.0
    DIVIDA_INICIAL = divida_inicial

    soma_renda = df_agentes["renda_bruta"].sum()
    soma_riq = df_agentes["riqueza_bruta"].sum()

    df_agentes = df_agentes.with_columns([
        (pl.col("renda_bruta") / soma_renda * PIB_INICIAL).alias("renda_trabalho"),
        (pl.col("riqueza_bruta") / soma_riq * DIVIDA_INICIAL).alias("riqueza"),
    ])

    return (
        jnp.array(df_agentes["decil"].to_numpy(), dtype=jnp.int32),
        jnp.array(df_agentes["renda_trabalho"].to_numpy(), dtype=jnp.float32),
        jnp.array(df_agentes["pmc"].to_numpy(), dtype=jnp.float32),
        jnp.array(df_agentes["riqueza"].to_numpy(), dtype=jnp.float32),
    )


# ==============================================================================
# 2. MOTOR DE SIMULAÇÃO HANK / ABM VETORIZADO EM JAX (48 MESES)
# ==============================================================================
def criar_simulador_jax(decil, renda_base, pmc, riqueza_base, parametros=None):
    mask_base = (decil <= 5).astype(jnp.float32)   # 50% mais pobres (alta PMC)
    mask_topo = (decil == 10).astype(jnp.float32)  # 10% mais ricos (detentores de títulos)

    TAU_BASE = 0.325
    G_PRIMARIO_0 = 32.9
    parametros = parametros or {}
    SELIC_0 = parametros.get("selic_inicial", 0.1375)
    DIVIDA_0 = parametros.get("divida_inicial", 82.9)
    CAMBIO_0 = parametros.get("cambio_inicial", 5.65)
    INFLACAO_0 = parametros.get("inflacao_inicial", 0.032)
    RESERVAS_0 = parametros.get("reservas_iniciais", 388.0)
    R_LEGADO_0 = parametros.get("juros_legados_iniciais", 0.115)
    SELIC_REFERENCIA = parametros.get("selic_referencia_cambio", 0.105)

    juros_0 = DIVIDA_0 * parametros.get("juros_efetivos_iniciais", 0.1268)
    y_disp_0 = (1.0 - TAU_BASE) * renda_base + (riqueza_base / DIVIDA_0) * juros_0
    C_0 = jnp.sum(pmc * y_disp_0 + 0.032 * riqueza_base)
    OUTROS_0 = 100.0 - C_0 - G_PRIMARIO_0

    @jax.jit
    def simular_cenario(
        trajetoria_selic: jnp.ndarray,
        ajuste_gasto_base: jnp.ndarray,
        aliquota_topo: jnp.ndarray,
        revisao_isencoes: jnp.ndarray,
        uso_reservas_bc: float,
    ):
        dt = 1.0 / 12.0

        def passo_mensal(carry, inputs):
            (
                riqueza,
                divida,
                nivel_precos,
                pib_real_ant,
                r_legado,
                cambio_ant,
            ) = carry

            selic_t, d_gasto_t, tau_topo_t, isencoes_t = inputs

            # 1. Custo efetivo da dívida (55% LFT cai na hora; 45% prefixado/IPCA rola em 36m)
            r_legado_novo = r_legado + (selic_t - r_legado) / 36.0
            r_efetivo = 0.55 * selic_t + 0.45 * r_legado_novo
            juros_divida = divida * r_efetivo

            # 2. Renda do trabalho, transferências na base e juros no topo
            fator_atividade = pib_real_ant / 100.0
            renda_trab_nom = renda_base * fator_atividade * nivel_precos

            peso_base = mask_base / jnp.sum(mask_base)
            transf_base = d_gasto_t * nivel_precos * peso_base

            juros_recebidos = (riqueza / (divida + 1e-6)) * juros_divida
            imposto_topo_indiv = tau_topo_t * juros_recebidos * mask_topo

            y_disp = (1.0 - TAU_BASE) * renda_trab_nom + juros_recebidos - imposto_topo_indiv + transf_base
            consumo_indiv = pmc * y_disp + 0.032 * riqueza
            C_nom = jnp.sum(consumo_indiv)
            C_real = C_nom / nivel_precos

            # 3. Câmbio e Setor Externo (choque de juros vs. escudo de US$ 388 bi)
            diferencial_juros = selic_t - SELIC_REFERENCIA
            pressao_especulativa = -8.0 * diferencial_juros
            fator_amortecimento = 1.0 - jnp.clip(0.82 * uso_reservas_bc * RESERVAS_0 / 388.0, 0.0, 1.0)
            cambio_t = CAMBIO_0 + pressao_especulativa * fator_amortecimento
            cambio_t = jnp.clip(cambio_t, CAMBIO_0 - 0.85, CAMBIO_0 + 1.15)

            # 4. Investimento Privado e PIB Real
            impulso_investimento = 1.0 + 0.65 * (C_real / C_0 - 1.0) - 0.35 * (selic_t - SELIC_0)
            efeito_cambio_nx = 0.8 * (cambio_t - CAMBIO_0)
            outros_real = OUTROS_0 * impulso_investimento + efeito_cambio_nx

            G_primario_real = G_PRIMARIO_0 + d_gasto_t
            pib_real_t = C_real + G_primario_real + outros_real

            # 5. Inflação (meta 3% + pressão de demanda + repasse cambial)
            hiato_produto = (pib_real_t - 100.0) / 100.0
            variacao_cambio = (cambio_t - cambio_ant) / cambio_ant
            inflacao_anual = INFLACAO_0 + 0.18 * jnp.maximum(hiato_produto, -0.03) + 0.08 * (variacao_cambio * 12.0)
            inflacao_anual = jnp.clip(inflacao_anual, 0.02, 0.12)
            nivel_precos_novo = nivel_precos * (1.0 + inflacao_anual * dt)

            pib_nom_t = pib_real_t * nivel_precos_novo

            # 6. Contas Públicas Endógenas
            arrecadacao_topo = jnp.sum(imposto_topo_indiv)
            arrecadacao_total = TAU_BASE * pib_nom_t + arrecadacao_topo + (isencoes_t * pib_nom_t)
            G_primario_nom = G_primario_real * nivel_precos_novo

            resultado_primario = arrecadacao_total - G_primario_nom
            resultado_nominal = resultado_primario - juros_divida

            divida_nova = divida - resultado_nominal * dt
            razao_divida_pib = 100.0 * (divida_nova / pib_nom_t)

            # 7. Consistência Fluxo-Estoque (SFC)
            poupanca_indiv = y_disp - consumo_indiv
            riqueza_bruta_nova = jnp.maximum(riqueza + poupanca_indiv * dt, 0.0)
            riqueza_nova = riqueza_bruta_nova * (divida_nova / (jnp.sum(riqueza_bruta_nova) + 1e-6))

            riq_d10 = jnp.mean(jnp.where(decil == 10, riqueza_nova, 0.0)) * 10.0
            riq_d1 = jnp.mean(jnp.where(decil == 1, riqueza_nova, 0.0)) * 10.0 + 1e-6
            razao_desigualdade = riq_d10 / riq_d1

            novo_carry = (
                riqueza_nova,
                divida_nova,
                nivel_precos_novo,
                pib_real_t,
                r_legado_novo,
                cambio_t,
            )

            metricas = (
                pib_real_t,
                razao_divida_pib,
                (resultado_primario / pib_nom_t) * 100.0,
                (juros_divida / pib_nom_t) * 100.0,
                inflacao_anual * 100.0,
                cambio_t,
                razao_desigualdade,
            )
            return novo_carry, metricas

        estado_inicial = (riqueza_base, DIVIDA_0, 1.0, 100.0, R_LEGADO_0, CAMBIO_0)
        inputs_scan = (trajetoria_selic, ajuste_gasto_base, aliquota_topo, revisao_isencoes)
        _, historico = jax.lax.scan(passo_mensal, estado_inicial, inputs_scan)
        return historico

    return simular_cenario


# ==============================================================================
# 3. EXECUÇÃO DOS CENÁRIOS E GERAÇÃO DE RELATÓRIO E GRÁFICOS
# ==============================================================================
if __name__ == "__main__":
    t0 = time.time()
    decil, renda_base, pmc, riqueza_base = gerar_populacao_agentes(n_agentes=1_000_000)
    simular = criar_simulador_jax(decil, renda_base, pmc, riqueza_base)

    # CENÁRIO A: Ortodoxo / Austeridade (Faria Lima / Focus)
    selic_ortodoxo = jnp.linspace(0.1375, 0.1150, 48)
    gasto_ortodoxo = jnp.linspace(-0.3, -1.5, 48)
    topo_ortodoxo = jnp.zeros(48)
    isencoes_ortodoxo = jnp.zeros(48)

    res_ort = simular(
        selic_ortodoxo, gasto_ortodoxo, topo_ortodoxo, isencoes_ortodoxo, uso_reservas_bc=0.0
    )

    # CENÁRIO B: Heterodoxo (Proposta Lara Resende / Manifesto HANK)
    selic_het = jnp.concatenate([
        jnp.linspace(0.1375, 0.0750, 12),
        jnp.linspace(0.0750, 0.0650, 36),
    ])
    gasto_het = jnp.linspace(0.2, 0.8, 48)
    topo_het = jnp.ones(48) * 0.10
    isencoes_het = jnp.linspace(0.005, 0.012, 48)

    res_het = simular(
        selic_het, gasto_het, topo_het, isencoes_het, uso_reservas_bc=1.0
    )

    jax.block_until_ready(res_het)
    elapsed = time.time() - t0

    pib_ort, div_ort, prim_ort, jur_ort, inf_ort, fx_ort, desig_ort = [np.array(x) for x in res_ort]
    pib_het, div_het, prim_het, jur_het, inf_het, fx_het, desig_het = [np.array(x) for x in res_het]

    print(f"\nSimulação de 1.000.000 de agentes (48 meses x 2 cenários) concluída em {elapsed:.2f}s!\n")
    print("=" * 78)
    print(f"{'INDICADOR (AO FINAL DE 4 ANOS)':<38} | {'ORTODOXO (AUSTER.)':<18} | {'HETERODOXO (HANK)':<18}")
    print("=" * 78)
    print(f"{'PIB Real (Base 100 inicial)':<38} | {pib_ort[-1]:>17.2f} | {pib_het[-1]:>17.2f}")
    print(f"{'Crescimento Acumulado do PIB (%)':<38} | {pib_ort[-1]-100:>16.2f}% | {pib_het[-1]-100:>16.2f}%")
    print(f"{'Dívida Bruta / PIB (%)':<38} | {div_ort[-1]:>16.2f}% | {div_het[-1]:>16.2f}%")
    print(f"{'Custo Anual dos Juros (% do PIB)':<38} | {jur_ort[-1]:>16.2f}% | {jur_het[-1]:>16.2f}%")
    print(f"{'Resultado Primário (% do PIB)':<38} | {prim_ort[-1]:>16.2f}% | {prim_het[-1]:>16.2f}%")
    print(f"{'Inflação Anualizada (%)':<38} | {inf_ort[-1]:>16.2f}% | {inf_het[-1]:>16.2f}%")
    print(f"{'Taxa de Câmbio (R$/US$)':<38} | R$ {fx_ort[-1]:>14.2f} | R$ {fx_het[-1]:>14.2f}")
    print("=" * 78)

    eixo_x = np.arange(1, 49)
    fig, axs = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Simulação HANK/ABM Brasil (1 Milhão de Agentes): Austeridade vs. Proposta Heterodoxa", fontsize=13, fontweight="bold")

    axs[0, 0].plot(eixo_x, pib_ort, label="Ortodoxo (Corte Primário + Selic Alta)", color="#d62728", lw=2.2)
    axs[0, 0].plot(eixo_x, pib_het, label="Heterodoxo (Selic 7,5% + Taxação Topo)", color="#1f77b4", lw=2.2)
    axs[0, 0].set_title("Trajetória do PIB Real (Índice Base 100)")
    axs[0, 0].grid(True, alpha=0.3)
    axs[0, 0].legend()

    axs[0, 1].plot(eixo_x, div_ort, label="Ortodoxo (Dívida/PIB)", color="#d62728", lw=2.2)
    axs[0, 1].plot(eixo_x, div_het, label="Heterodoxo (Dívida/PIB)", color="#1f77b4", lw=2.2)
    axs[0, 1].set_title("Relação Dívida Bruta / PIB (%)")
    axs[0, 1].grid(True, alpha=0.3)
    axs[0, 1].legend()

    axs[1, 0].plot(eixo_x, jur_ort, label="Ortodoxo (Juros % PIB)", color="#d62728", lw=2.2)
    axs[1, 0].plot(eixo_x, jur_het, label="Heterodoxo (Juros % PIB)", color="#1f77b4", lw=2.2)
    axs[1, 0].set_title("Peso do Serviço da Dívida (% do PIB)")
    axs[1, 0].set_xlabel("Meses")
    axs[1, 0].grid(True, alpha=0.3)
    axs[1, 0].legend()

    axs[1, 1].plot(eixo_x, fx_ort, label="Ortodoxo (Câmbio Passivo)", color="#d62728", lw=2.2)
    axs[1, 1].plot(eixo_x, fx_het, label="Heterodoxo (Escudo US$ 388 bi)", color="#1f77b4", lw=2.2)
    axs[1, 1].set_title("Taxa de Câmbio (R$ / US$)")
    axs[1, 1].set_xlabel("Meses")
    axs[1, 1].grid(True, alpha=0.3)
    axs[1, 1].legend()

    plt.tight_layout()
    plt.savefig("comparativo_hank_brasil.png", dpi=150)
    print("\nGráfico salvo com sucesso em: comparativo_hank_brasil.png")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
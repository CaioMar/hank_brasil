# AGENTS.md — Arquitetura e Propósito: Modelagem Macroeconômica Heterodoxa (HANK / ABM)

## 1. Propósito Científico e Problema de Negócio
Este projeto desenvolve um motor computacional de alta performance em **Econofísica e Macroeconomia Computacional** para simular a economia brasileira e gerar projeções alternativas (*Nowcasting* e *Backtesting*).

### Por que este modelo existe?
Os modelos macroeconômicos tradicionais utilizados pelo consenso do mercado financeiro (Relatório Focus, grandes bancos comerciais e modelos DSGE/RANK — *Representative Agent New Keynesian*) cometem erros sistemáticos de previsão (subestimando o crescimento do PIB e superestimando o efeito positivo de cortes de gastos) porque:
1. **Assumem um "Agente Representativo" médio:** Ignoram a distribuição de renda e riqueza, tratando o consumo de um trabalhador de baixa renda como idêntico ao de um rentista.
2. **Trataram a arrecadação como exógena:** Prescrevem austeridade fiscal (corte de gastos primários) como solução única, ignorando que cortar gastos reduz a demanda efetiva, encolhe o PIB, derruba a arrecadação tributária e **piora** a relação Dívida/PIB (como ocorreu no Brasil entre 2015 e 2018).
3. **Invertem a causalidade da dívida:** Ignoram que, no Brasil, o crescimento explosivo da dívida pública decorre do custo financeiro da taxa Selic elevada ($r > g$) incidente sobre títulos pós-fixados (LFTs), e não do gasto social primário.

Nosso objetivo é substituir o agente representativo por **milhões de agentes heterogêneos (HANK / ABM)** vetorizados em GPU/CPU via `JAX`, calibrados com microdados reais via `Polars`.

---

## 2. Fundamentos Teóricos e Mecanismos Causais (Invariantes do Modelo)
Ao modificar, expandir ou refatorar qualquer módulo deste repositório, o agente de código **deve preservar** os seguintes mecanismos econômicos:

1. **Heterogeneidade da Propensão Marginal a Consumir (PMC):**
   - Os decis inferiores de renda (D1 a D5) possuem $\text{PMC} \in [0.80, 0.95]$ (consomem quase toda a renda marginal).
      - O topo da pirâmide (D10) possui $\text{PMC} \in [0.10, 0.20]$ e concentra a posse da dívida pública financeira.
         - *Consequência:* Transferências ou ganho real do salário mínimo na base possuem multiplicador fiscal $k > 1.5$. Tributar dividendos/altas rendas no topo tem impacto quase nulo sobre o consumo agregado.

         2. **Endogenia Fiscal e Consistência Fluxo-Estoque (SFC):**
            - A receita tributária ($T_t = \tau \cdot Y_t + T_{\text{topo}} + T_{\text{isenções}}$) responde endogenamente ao nível de atividade econômica ($Y_t$).
               - Todo fluxo financeiro (juros pagos pelo Tesouro, impostos recolhidos, salários, transferências) deve fechar contabilmente nos balanços dos agentes e do setor público, sem vazamentos artificiais.

               3. **Estrutura da Dívida Pública e Canal das LFTs (Teoria Fiscal do Nível de Preços / Lara Resende):**
                  - Cerca de 55% da dívida pública brasileira é indexada à Selic diária (LFTs). Portanto, cortes na taxa básica reduzem o serviço da dívida quase imediatamente, gerando economia fiscal real sem necessidade de recessão.

                  4. **Setor Externo, Derivativos e Escudo de Reservas:**
                     - A taxa de câmbio ($\text{R\$}/\text{US\$}$) sofre pressões especulativas de curto prazo via diferencial de juros e mercado de derivativos (B3).
                        - O Banco Central dispõe de reservas internacionais (~US$ 388 bilhões) capazes de amortecer a volatilidade cambial e neutralizar o repasse inflacionário (*pass-through*) durante ciclos de queda da Selic.

                        5. **Conflito de Funções Objetivo:**
                           - O modelo permite comparar a **Função de Perda Ortodoxa** (foco estrito em meta de inflação de 3%, $r > g$ e corte de despesas obrigatórias) contra a **Função de Perda Social/Desenvolvimentista** (pleno emprego, crescimento da massa salarial, redução de desigualdade e convergência de $r \approx g$).

                           ---

                           ## 3. Diretrizes de Flexibilidade e Evolução para o Agente
                           Se durante o desenvolvimento surgirem novas fontes de dados, variáveis ou hipóteses, siga estas regras de engenharia:

                           - **Ingestão de Microdados Reais (`Polars`):**
                             - Caso o usuário adicione arquivos brutos da **POF** (Pesquisa de Orçamentos Familiares) ou **PNAD Contínua** do IBGE na pasta `data/`, substitua a geração sintética de decis por pipelines *lazy* em `Polars` (`pl.scan_csv` / `pl.scan_parquet`), preservando a interface de saída de vetores JAX (`decil`, `renda_trabalho`, `pmc`, `riqueza`).
                             - **Séries Temporais Reais (`BCB SGS`):**
                               - Caso o usuário conecte a API do Sistema Gerenciador de Séries Temporais do Banco Central (Selic, IPCA, Dívida Bruta/PIB, Reservas Internacionais, Câmbio PTAX), utilize esses dados para calibrar as condições iniciais ($t=0$) e rodar janelas de *backtesting* histórico (ex: 2015–2018 e 2023–2026).
                               - **Performance e Diferenciabilidade (`JAX`):**
                                 - Mantenha o núcleo da simulação livre de loops Python sobre agentes ou passos temporais. Utilize `@jax.jit` e `jax.lax.scan` para que $N \ge 10^6$ agentes executem em milissegundos.
                                   - Mantenha todas as equações de transição diferenciáveis (usando `jnp.where`, `jnp.clip` ou aproximações suaves) para permitir calibração automática de parâmetros via gradiente (`jax.grad` / `optax`) contra dados históricos realizados.
                                   - **Novos Setores / Agentes:**
                                     - Ao expandir o modelo (ex: incluir setor bancário/operações compromissadas, crédito corporativo ou restrição externa por elasticidade de importação), modularize em funções puras dentro de `src/models/` e registre as premissas nos gráficos de saída.

                                     ---

                                     ## 4. Estrutura Recomendada do Workspace
                                     ```text
                                     hank_brasil/
                                     ├── AGENTS.md                  # Este documento (contexto teórico e regras de engenharia)
                                     ├── simulacao_hank_brasil.py   # Motor inicial autocontido (1M agentes, 48 meses)
                                     ├── data/                      # Microdados IBGE (POF/PNAD) e séries BCB SGS (Parquet)
                                     └── src/
                                         ├── etl/                   # Pipelines Polars para limpeza e calibração micro
                                             ├── models/                # Equações de transição JAX (Famílias, Governo, BC, Câmbio)
                                                 └── backtest/              # Validação Out-of-Sample e teste Diebold-Mariano vs. Focus


                                                 ---

                                                 ### 2. Instalação e Código Executável (`simulacao_hank_brasil.py`)

                                                 No terminal do seu desktop, crie a pasta e instale as dependências:

                                                 ```bash
                                                 mkdir hank_brasil && cd hank_brasil
                                                 python -m venv .venv
                                                 source .venv/bin/activate  # No Windows PowerShell: .venv\Scripts\Activate.ps1
                                                 pip install --upgrade pip polars jax matplotlib numpy
                                                 
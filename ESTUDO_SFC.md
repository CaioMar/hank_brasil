# Experimento de fechamento contábil

## Objetivo e escopo

O módulo `src/models/sfc.py` é um protótipo separado do motor original. Ele testa uma economia fechada simplificada em que famílias detêm ativos financeiros líquidos e o governo emite dívida. Não substitui os resultados anteriores, não é uma versão validada da economia brasileira e não é um modelo HANK completo.

A demanda é a soma do consumo das famílias, de compras do governo e, opcionalmente, de um gasto privado autônomo. Toda a renda gerada pela produção é distribuída às famílias em proporções fixas. Os impostos são debitados das famílias e creditados ao governo; juros e transferências têm as mesmas contrapartidas. As famílias pagam também o gasto privado autônomo. A variação de seus ativos líquidos é a poupança, sem piso zero ou reescala artificial.

Os fluxos são anualizados e os estoques evoluem em passos mensais. A identidade entre ativos agregados e dívida depende de serem iguais no início. Ativos negativos representam passivos financeiros líquidos das famílias; uma posição individual negativa não é uma posse negativa de títulos públicos. O protótipo supõe que esses passivos sejam compensados por direitos de outras famílias, remunerados à mesma taxa da dívida pública. Não existem restrições de crédito, inadimplência, carteira explícita, retenção de lucros, capital produtivo, sistema bancário ou setor externo. Não se demonstrou fechamento dos setores omitidos.

## Duas hipóteses para a demanda

- **Sem ancoragem:** gasto privado autônomo igual a zero. Como o modelo não representa outros componentes da demanda, o PIB simulado fica muito abaixo da referência inicial.
- **Com ancoragem:** adiciona-se um gasto privado autônomo hipotético e constante em termos reais, pago pelas famílias e dimensionado para que a soma dos componentes de demanda no instante inicial seja 100. Não é uma série observada de investimento nem um parâmetro estimado; a hipótese altera também a poupança. O PIB do primeiro mês pode diferir de 100 devido à inflação.

Ambas as versões usam Selic e IPCA mensais realizados ao longo da janela. A inflação é uma entrada exógena; ao contrário do motor original, este experimento não calcula câmbio ou inflação. Por usar dados futuros realizados e séries potencialmente revisadas, **não é previsão fora da amostra nem comparação justa com o Focus**. Os 100 mil agentes e suas PMCs são sintéticos.

## Resultados exploratórios

Erro absoluto médio (EAM) em pontos percentuais da dívida/PIB, de fevereiro do ano inicial até dezembro do ano final. Os resíduos de estoque são máximos absolutos na escala nominal com PIB inicial de referência 100, não em reais nem em pontos percentuais.

| Janela | Hipótese | Dívida/PIB simulada final | Observada final | EAM | Resíduo máximo entre ativos e dívida | Agentes com ativos negativos no fim |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2015–2018 | Sem ancoragem | 234,89% | 75,27% | 100,60 | 0,000015 | 0,00% |
| 2015–2018 | Com ancoragem | 75,39% | 75,27% | 3,99 | 0,000031 | 70,13% |
| 2023–2025 | Sem ancoragem | 225,55% | 78,64% | 104,24 | 0,000031 | 0,00% |
| 2023–2025 | Com ancoragem | 93,16% | 78,64% | 6,76 | 0,000023 | 64,41% |

O resultado próximo da dívida observada em dezembro de 2018, na versão ancorada, não comprova precisão ou causalidade. A diferença entre versões é consequência de uma hipótese de gasto não observada, e as taxas elevadas de agentes com ativos negativos expõem a ausência de restrição de crédito. A dívida, o PIB e os balanços dependem fortemente dessas simplificações. O fechamento é uma propriedade das equações desta economia artificial, não uma validação das premissas.

Uma execução separada com um milhão de agentes, 47 meses, na versão ancorada de 2015–2018, terminou neste ambiente em aproximadamente 1,06 segundo, incluindo inicialização e compilação. É uma medição isolada, não uma garantia de desempenho em outras máquinas.

## Reprodução

```bash
MPLBACKEND=Agg python -m src.relatorio.experimento_sfc --dados data/sgs --agentes 100000 --saida data/sgs/experimento_sfc.parquet
MPLBACKEND=Agg python -m src.relatorio.experimento_sfc --dados data/sgs --agentes 100000 --ancorar-pib --saida data/sgs/experimento_sfc_ancorado.parquet
MPLBACKEND=Agg python -m src.relatorio.experimento_sfc --dados data/sgs_2023_2025 --agentes 100000 --saida data/sgs_2023_2025/experimento_sfc.parquet
MPLBACKEND=Agg python -m src.relatorio.experimento_sfc --dados data/sgs_2023_2025 --agentes 100000 --ancorar-pib --saida data/sgs_2023_2025/experimento_sfc_ancorado.parquet
python -m unittest discover -s tests
```

## Próximos problemas

Modelar investimento, empresas, bancos e crédito com balanços e contrapartidas explícitas; obter dados para inicializar seus estoques; incorporar restrições de crédito sem criar recursos artificialmente; e comparar trajetórias sob hipóteses observáveis. Só depois faz sentido avaliar calibração estrutural e previsões com informações disponíveis na época. A auditoria do motor original continua válida.
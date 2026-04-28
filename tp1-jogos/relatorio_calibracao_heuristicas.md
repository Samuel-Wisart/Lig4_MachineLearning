# Relatório de Calibração da Heurística

## Objetivo

Este teste comparou duas variações da heurística do agente de Connect Four usando apenas `iterative_deepening`:

- **baseline**: heurística completa, com os fatores de future habilitados.
- **no_future**: mesma heurística, mas com `use_future=False`, ignorando a parte de future scoring.

O foco foi verificar se o cálculo de future compensa em qualidade de jogo e se ele justifica o custo adicional de avaliação.

## Configuração

- Agente testado: `choose_move_iterative_deepening`
- Tempos de teste: **1 s**, **2 s** e **3 s**
- Profundidade máxima usada no teste curto: **5**
- Jogos por lado em cada tempo: **1**
- Total por tempo: **2 partidas**
- Alternância de cores:
  - partida 1: baseline como vermelho, no_future como amarelo
  - partida 2: no_future como vermelho, baseline como amarelo

## Metodologia

As partidas foram executadas fora do site, em um script separado, para acelerar os testes. Em cada turno, a coluna era escolhida por `choose_move_iterative_deepening`, alterando apenas o parâmetro `use_future` entre as duas variantes.

O resultado foi medido em pontos de match:

- vitória: 1 ponto
- empate: 0,5 ponto
- derrota: 0 ponto

## Resultados

| Tempo | Variante | Pontos | Vitórias | Derrotas | Empates | Tempo médio por jogo (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1s | baseline | 2.0 | 2 | 0 | 0 | 2786.1 |
| 1s | no_future | 0.0 | 0 | 2 | 0 | 2509.6 |
| 2s | baseline | 2.0 | 2 | 0 | 0 | 2809.8 |
| 2s | no_future | 0.0 | 0 | 2 | 0 | 2493.4 |
| 3s | baseline | 2.0 | 2 | 0 | 0 | 2800.6 |
| 3s | no_future | 0.0 | 0 | 2 | 0 | 2507.0 |

## Leitura dos resultados

1. A variante **baseline** venceu todas as partidas do teste curto.
2. A variante **no_future** foi consistentemente mais fraca, mesmo sendo um pouco mais rápida.
3. Neste conjunto de testes, o ganho estratégico do cálculo de future compensou a pequena perda de tempo.
4. Os tempos médios ficaram próximos de 2,5 s a 2,8 s porque a busca foi limitada por profundidade (`max_depth=5`) antes de usar completamente os 1 s, 2 s e 3 s em várias posições.

## Conclusão

Com base neste teste curto, a melhor configuração é **manter o cálculo de future habilitado**.

Em termos práticos:

- **Se o objetivo for força de jogo:** manter `FUTURE_THREE_FACTOR` e `FUTURE_TWO_FACTOR` ativos.
- **Se o objetivo for reduzir custo de avaliação:** `use_future=False` acelera um pouco, mas neste teste perdeu qualidade de jogo.

## Observação

Este relatório usa uma amostra pequena para validação rápida. Para uma calibração mais forte, o ideal é aumentar `--games-per-side` e também elevar `--max-depth` para deixar o tempo de busca pesar mais do que o limite de profundidade.
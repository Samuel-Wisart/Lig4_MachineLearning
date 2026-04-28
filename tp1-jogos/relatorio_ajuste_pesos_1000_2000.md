# Relatório de Ajuste de Pesos da Heurística

## Objetivo

Este ajuste buscou calibrar a heurística do agente usando apenas `iterative_deepening`, com foco em dois orçamentos de tempo:

- 1000 ms
- 2000 ms

O objetivo foi encontrar uma configuração de pesos mais adequada para cada janela de tempo, sem alterar `server.py`.

## Método

Foi feita uma busca coordenada por self-play:

- uma variante candidata jogava contra a configuração corrente;
- a avaliação era repetida com as cores invertidas;
- o melhor candidato por dimensão era mantido;
- o processo foi executado separadamente para 1000 ms e 2000 ms.

Parâmetros do teste:

- agente: `choose_move_iterative_deepening`
- profundidade máxima: 5
- jogos por lado: 1
- comparação apenas por self-play entre perfis da heurística

## Configuração Base

Os pesos originais usados como ponto de partida foram:

- `WIN_SCORE = 100000`
- `THREE_IN_A_ROW_SCORE = 100`
- `TWO_IN_A_ROW_SCORE = 10`
- `CENTER_COLUMN_SCORE = 6`
- `OPP_THREE_PENALTY = 120`
- `OPP_TWO_PENALTY = 12`
- `FUTURE_THREE_FACTOR = 0.35`
- `FUTURE_TWO_FACTOR = 0.5`

## Resultado do Ajuste

### Perfil recomendado para 1000 ms

- `WIN_SCORE = 100000`
- `THREE_IN_A_ROW_SCORE = 108`
- `TWO_IN_A_ROW_SCORE = 11`
- `CENTER_COLUMN_SCORE = 5`
- `OPP_THREE_PENALTY = 110`
- `OPP_TWO_PENALTY = 11`
- `FUTURE_THREE_FACTOR = 0.4025`
- `FUTURE_TWO_FACTOR = 0.575`

### Perfil recomendado para 2000 ms

- `WIN_SCORE = 100000`
- `THREE_IN_A_ROW_SCORE = 92`
- `TWO_IN_A_ROW_SCORE = 9`
- `CENTER_COLUMN_SCORE = 5`
- `OPP_THREE_PENALTY = 130`
- `OPP_TWO_PENALTY = 13`
- `FUTURE_THREE_FACTOR = 0.4025`
- `FUTURE_TWO_FACTOR = 0.575`

## Leitura dos Resultados

1. O ajuste convergiu para uma coluna central um pouco menos agressiva, reduzindo `CENTER_COLUMN_SCORE` para 5 nas duas janelas.
2. Para 1000 ms, a busca favoreceu uma heurística um pouco mais ofensiva, com `THREE_IN_A_ROW_SCORE = 108` e `TWO_IN_A_ROW_SCORE = 11`.
3. Para 2000 ms, a configuração vencedora ficou mais defensiva, com penalidades maiores para ameaça do oponente.
4. O fator de future ficou acima do ponto inicial em ambos os casos, indicando que essa parte da heurística continua valendo o custo.

## Conclusão

O ajuste prático recomendado é usar perfis diferentes conforme o tempo disponível:

- **1000 ms**: perfil com mais peso ofensivo.
- **2000 ms**: perfil com mais peso defensivo.

No `search.py`, a seleção automática já foi ligada ao `max_time_ms`, então o agente usa o perfil correspondente sem depender de mudanças em `server.py`.

## Observação

Este é um ajuste local e prático, baseado em amostra curta de self-play. Para uma calibração mais robusta, o próximo passo seria aumentar o número de jogos por comparação e testar mais pontos intermediários de tempo.
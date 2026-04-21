# TP1 - Ligue-4 com Busca Adversarial

Este arquivo descreve, de forma detalhada, como o agente de IA do projeto será construído e como cada função deve funcionar. A ideia é implementar o agente em etapas pequenas, validando cada parte antes de avançar para a seguinte.

O objetivo final é ter um agente capaz de jogar Ligue-4 usando:

1. Validação do ambiente e jogadas aleatórias.
2. Função de avaliação heurística.
3. Minimax com profundidade limitada.
4. Poda Alfa-Beta.
5. Iterative Deepening com limite de tempo.

## 1. Visão geral do funcionamento

O servidor Flask chama a função `choose_move(board, turn, config)` em `search.py`. Essa função recebe o estado atual do tabuleiro, o jogador da vez e os parâmetros de controle definidos na interface web.

### Entrada da função principal

- `board`: matriz `6 x 7` com valores:
  - `0` = casa vazia
  - `1` = peça do Jogador 1
  - `2` = peça do Jogador 2
- `turn`: jogador que deve jogar agora, `1` ou `2`
- `config`: dicionário com parâmetros da jogada:
  - `max_time_ms`: tempo máximo por jogada em milissegundos
  - `max_depth`: profundidade máxima permitida na busca

### Saída esperada

`choose_move` deve retornar:

- a coluna escolhida, entre `0` e `6`
- um dicionário `info` com informações de depuração e métricas

Exemplo de retorno esperado:

```python
return 3, {
    "method": "alphabeta",
    "depth_reached": 4,
    "nodes_expanded": 1824,
    "score": 124
}
```

O servidor já possui proteção contra travamentos e timeout rígido. Mesmo assim, o agente deve tentar respeitar o tempo limite e sempre devolver uma jogada válida quando possível.

## 2. Estrutura atual do projeto

Os arquivos relevantes do TP1 são:

- `server.py`: servidor web em Flask que expõe a interface e chama o agente.
- `search.py`: onde a IA será implementada.
- `templates/index.html`: interface do jogo.
- `static/sketch.js`: lógica visual e comunicação com o servidor.

No estado atual, `search.py` já contém funções utilitárias prontas para trabalhar com o tabuleiro:

- `copy_board`
- `valid_moves`
- `make_move`
- `winner`
- `is_full`
- `terminal`
- `other`

Essas funções serão reaproveitadas em todas as etapas da IA.

## 3. Objetivo de implementação em etapas

A implementação será feita em ordem incremental. Isso é importante porque cada etapa depende da anterior e permite testar comportamento e desempenho aos poucos.

### Etapa 1 - Validação básica e jogada aleatória

Objetivo: confirmar que o agente está conectado ao servidor e que consegue devolver uma coluna válida.

Funções envolvidas:

- `choose_move_randomly`
- `choose_move`

Comportamento esperado:

- verificar movimentos válidos com `valid_moves`
- escolher uma coluna aleatória entre as válidas
- retornar a jogada sem tentar pensar

Essa etapa serve para baseline e para garantir que a integração cliente-servidor está funcionando.

### Etapa 2 - Função de avaliação heurística

Objetivo: criar uma forma de estimar se um tabuleiro é bom ou ruim para um jogador, mesmo quando a partida ainda não terminou.

Funções envolvidas:

- `evaluate_board`
- `score_window`
- `count_patterns` ou funções auxiliares equivalentes

Comportamento esperado:

- detectar vitória, derrota e empate
- valorizar o centro do tabuleiro
- contar sequências de 2, 3 e 4 peças
- penalizar ameaças do oponente

Essa etapa é a base de todo o resto. Sem heurística boa, o Minimax vai tomar decisões fracas.

### Etapa 3 - Minimax com profundidade limitada

Objetivo: explorar jogadas futuras com alternância entre maximizar e minimizar a avaliação.

Funções envolvidas:

- `minimax`
- `choose_move`

Comportamento esperado:

- parar em estados terminais
- parar quando a profundidade limite é atingida
- usar a função heurística quando não puder continuar expandindo
- escolher a jogada que maximiza a chance de vitória do agente

### Etapa 4 - Poda Alfa-Beta

Objetivo: reduzir o número de nós visitados sem mudar a resposta final do Minimax.

Funções envolvidas:

- `alphabeta`
- `choose_move`

Comportamento esperado:

- manter os mesmos valores do Minimax
- cortar ramos que não podem melhorar a decisão final
- registrar métricas como número de nós visitados

### Etapa 5 - Iterative Deepening

Objetivo: melhorar o uso do tempo disponível e manter sempre a melhor jogada encontrada até o momento.

Funções envolvidas:

- `iterative_deepening`
- `alphabeta`
- `choose_move`

Comportamento esperado:

- rodar profundidade 1, depois 2, depois 3 e assim por diante
- parar quando atingir `max_depth` ou o limite de tempo
- guardar a melhor jogada da última profundidade concluída com sucesso

### Etapa 6 - Ajustes para competição

Objetivo: aumentar a força da IA sem quebrar o limite de tempo.

Melhorias possíveis:

- ordenação de movimentos, priorizando a coluna central
- tabela de transposição
- heurística mais refinada
- corte de jogadas obviamente ruins
- reaproveitamento de resultados entre profundidades

## 4. Funções que serão criadas e seu papel

Esta seção detalha cada função que provavelmente será adicionada ao `search.py`.

### 4.1 `choose_move(board, turn, config)`

Função principal chamada pelo servidor.

Responsabilidades:

- ler `max_time_ms` e `max_depth`
- gerar os movimentos possíveis
- decidir qual estratégia usar
- retornar uma coluna válida
- devolver um dicionário com métricas úteis

Nesta função, a implementação final deve chamar a versão evoluída da IA. Inicialmente, ela pode apenas chamar a jogada aleatória para testes. Depois, ela passará a chamar `iterative_deepening` ou `alphabeta`.

### 4.2 `choose_move_randomly(board, turn, config)`

Função de baseline.

Responsabilidades:

- listar as colunas válidas
- escolher uma delas aleatoriamente
- servir como referência mínima de funcionamento

Uso prático:

- validar se o jogo roda sem erros
- confirmar comunicação com o servidor
- comparar o comportamento da IA inteligente com uma estratégia simples

### 4.3 `valid_moves(board)`

Função utilitária já existente.

Responsabilidades:

- retornar todas as colunas em que ainda é possível jogar

Regra usada:

- uma coluna está disponível se a célula do topo dela ainda estiver vazia

Essa função evita que a IA tente jogar em colunas cheias.

### 4.4 `make_move(board, col, player)`

Função utilitária já existente.

Responsabilidades:

- criar um novo tabuleiro com a jogada aplicada
- respeitar a gravidade do Connect Four
- retornar `None` se a jogada for inválida

Ela será usada pelo Minimax e pelo Alfa-Beta para simular futuros estados do jogo sem alterar o tabuleiro original.

### 4.5 `winner(board)`

Função utilitária já existente.

Responsabilidades:

- detectar vitória horizontal
- detectar vitória vertical
- detectar vitória diagonal crescente e decrescente

Retorno:

- `0` se ninguém venceu
- `1` se o jogador 1 venceu
- `2` se o jogador 2 venceu

### 4.6 `terminal(board)`

Função utilitária já existente.

Responsabilidades:

- verificar se o jogo acabou
- identificar vitória ou empate

Retorno:

- `(True, vencedor)` se o estado for terminal
- `(False, 0)` caso contrário

Essa função é essencial para parar a busca nos nós finais.

### 4.7 `evaluate_board(board, player)`

Função heurística principal que será criada.

Responsabilidades:

- atribuir pontuação ao tabuleiro do ponto de vista de `player`
- devolver valor muito alto para vitória
- devolver valor muito baixo para derrota
- devolver valores intermediários para posições favoráveis ou perigosas

Componentes esperados:

- incentivo ao centro
- sequências abertas de 2, 3 e 4
- bloqueio de ameaças do oponente
- penalização para posições em que o adversário tem muitas chances imediatas

Sugestão de interpretação:

- pontuação positiva favorece o jogador atual
- pontuação negativa favorece o oponente

### 4.8 `score_window(window, player)`

Função auxiliar da heurística.

Responsabilidades:

- analisar uma janela de 4 casas consecutivas
- contar peças do jogador e do oponente
- atribuir peso conforme a configuração encontrada

Exemplos de janelas úteis:

- 4 peças do jogador: vitória
- 3 peças do jogador e 1 vazia: ameaça forte
- 2 peças do jogador e 2 vazias: potencial moderado
- 3 peças do oponente e 1 vazia: perigo que merece punição

### 4.9 `minimax(board, depth, maximizing_player, player)`

Função de busca adversarial sem poda.

Responsabilidades:

- explorar todas as jogadas possíveis até a profundidade limite
- alternar entre maximizar e minimizar o valor
- usar heurística quando a profundidade terminar

Essa função é a base conceitual da IA. Mesmo que a versão final use Alfa-Beta e Iterative Deepening, Minimax precisa existir para validar a lógica.

### 4.10 `alphabeta(board, depth, alpha, beta, maximizing_player, player)`

Versão otimizada do Minimax.

Responsabilidades:

- fazer tudo o que o Minimax faz
- cortar ramos que não podem influenciar a decisão
- manter exatamente a mesma escolha final do Minimax ideal

Parâmetros clássicos:

- `alpha`: melhor valor garantido para o maximizador
- `beta`: melhor valor garantido para o minimizador

### 4.11 `iterative_deepening(board, player, config)`

Busca progressiva com tempo controlado.

Responsabilidades:

- executar busca com profundidade crescente
- guardar a melhor jogada concluída em cada rodada
- parar antes de estourar o tempo máximo

Essa função é especialmente importante na competição, porque o tempo por jogada será rígido.

### 4.12 Funções auxiliares possíveis

Dependendo da organização final, talvez seja útil separar mais algumas rotinas:

- `ordered_moves(board)`: retorna jogadas ordenadas por prioridade
- `time_exceeded(start_time, max_time_ms)`: checa limite de tempo
- `copy_board`: clona o tabuleiro para simulação
- `get_next_open_row`: encontra a linha onde a peça cairá em uma coluna
- `center_column_score`: calcula o bônus da coluna central

## 5. Estratégia de implementação passo a passo

Para manter o projeto controlado, a implementação será feita nesta ordem:

### Passo 1 - Baseline funcional

Primeiro, vamos garantir que `choose_move_randomly` funciona e que `choose_move` pode chamar essa lógica sem quebrar o servidor.

O que será validado:

- o jogo abre no navegador
- a IA retorna uma coluna válida
- o tabuleiro avança normalmente
- não há erro de comunicação com o Flask

### Passo 2 - Heurística

Depois vamos criar a função de avaliação.

O que será validado:

- tabuleiros com vitória têm valor extremo
- tabuleiros com ameaça de vitória também recebem pontuações fortes
- posições centrais recebem bônus
- oponente com ameaça aberta recebe penalidade

### Passo 3 - Minimax simples

Com a heurística pronta, implementamos Minimax com profundidade limitada.

O que será validado:

- a IA enxerga mais de um lance à frente
- o código respeita `max_depth`
- estados terminais encerram a busca corretamente

### Passo 4 - Alfa-Beta

Depois substituímos a busca pura por Alfa-Beta.

O que será validado:

- a jogada escolhida continua coerente com o Minimax
- o número de nós expandidos diminui
- o tempo médio por jogada melhora

### Passo 5 - Iterative Deepening

Por fim, conectamos o tempo máximo à busca.

O que será validado:

- a IA devolve resposta antes do timeout rígido
- profundidades maiores são exploradas quando há tempo
- a melhor jogada parcial é preservada se o tempo acabar

## 6. Métricas que serão registradas

Para o relatório, idealmente o agente deve coletar e devolver algumas métricas por jogada ou por partida.

### Métricas principais

- `nodes_expanded`: número de nós visitados durante a busca
- `depth_reached`: profundidade máxima atingida
- `elapsed_ms`: tempo gasto na jogada
- `score`: avaliação final do lance escolhido
- `best_col`: coluna escolhida ao final da busca

### Métricas para o relatório

- taxa de vitória
- taxa de empate
- tempo médio por jogada
- média de estados visitados
- profundidade média atingida

## 7. Como o relatório deve ser pensado

O relatório final deve explicar a evolução do agente, não apenas mostrar resultados.

### Estrutura sugerida

1. Introdução e objetivo do TP1.
2. Metodologia de construção da IA.
3. Experimentos e resultados.
4. Discussão crítica.
5. Conclusão.

### Linha narrativa recomendada

O texto deve mostrar esta progressão:

- primeiro, um agente aleatório para garantir o ambiente
- depois, uma heurística que reconhece tabuleiros promissores
- em seguida, Minimax para raciocínio estratégico
- depois, Alfa-Beta para eficiência
- por fim, Iterative Deepening para lidar com o limite de tempo

## 8. Plano prático de execução nesta conversa

Vamos trabalhar em blocos pequenos.

### Ordem de implementação que vou seguir com você

1. Definir e testar a função de avaliação heurística.
2. Implementar Minimax com profundidade limitada.
3. Acrescentar Alfa-Beta.
4. Acrescentar Iterative Deepening.
5. Ajustar métricas e formato do retorno.
6. Rodar testes e comparar comportamento.

### Regra de trabalho

Em cada etapa:

- eu explico o que a função faz
- eu implemento somente aquela parte
- eu valido se o código continua funcionando
- só então avançamos para a próxima

## 9. Estado atual do projeto

Neste momento:

- o servidor já está pronto para chamar o agente
- as funções utilitárias de tabuleiro já existem
- a heurística, Minimax, Alfa-Beta e Iterative Deepening já estão implementados
- a IA padrão do aluno é `AI_Student`, que usa Iterative Deepening sobre Alfa-Beta
- existem modos específicos para comparação: `AI_Minimax`, `AI_AlphaBeta`, `AI_Random` e `AI_Dummy`

## 10. Versões do agente e comparação experimental

O projeto foi organizado para que a comparação entre estratégias fique clara tanto na interface quanto no relatório.

### Agentes disponíveis

- `AI_Random`: escolhe uma jogada válida aleatória
- `AI_Dummy`: escolhe uma jogada válida simples, usada como fallback
- `AI_Minimax`: usa busca Minimax sem poda
- `AI_AlphaBeta`: usa Minimax com poda Alfa-Beta
- `AI_Student`: usa Iterative Deepening com Alfa-Beta, sendo a versão principal do trabalho

### O que comparar no relatório

O relatório pode destacar a evolução em três níveis:

- Baseline: aleatório e dummy
- Busca exata limitada: Minimax e Alfa-Beta
- Busca adaptada ao tempo: Iterative Deepening

### Interpretação esperada

- Minimax deve ser mais lento e visitar mais nós
- Alfa-Beta deve reduzir os nós visitados sem mudar a decisão ideal
- Iterative Deepening deve respeitar melhor o tempo e entregar a melhor jogada concluída até o momento

## 11. Decisões de projeto já adotadas

Essas decisões são úteis para justificar escolhas metodológicas no texto do relatório.

### Heurística

- valoriza o centro do tabuleiro
- avalia janelas de 4 casas em horizontal, vertical e diagonal
- prioriza ameaças imediatas e também ameaças futuras com peso reduzido
- penaliza sequências perigosas do oponente

### Busca

- Minimax é usado como referência conceitual
- Alfa-Beta é a versão otimizada da busca principal
- Iterative Deepening é usado para lidar com o limite de tempo rígido
- a ordenação de jogadas privilegia a coluna central, o que costuma melhorar a poda

### Controle de tempo

- o agente não deve depender de um timeout perfeito para terminar bem
- o servidor impõe um hard timeout e também um fallback
- quando uma jogada inválida ou um timeout extremo ocorre, o servidor escolhe uma jogada válida aleatória

## 12. Estrutura recomendada para o relatório

Esta seção foi pensada para facilitar a transformação do README em texto de LaTeX.

### 12.1 Introdução

Explique o problema do Connect Four como um jogo de informação perfeita, determinístico e de soma zero. Destaque que o objetivo é implementar um agente de busca adversarial capaz de competir sob restrição de tempo.

### 12.2 Objetivo

Descreva que o trabalho busca comparar estratégias de busca, medir custo computacional e avaliar o impacto da heurística no desempenho do agente.

### 12.3 Metodologia

Explique a evolução do agente em ordem:

1. baseline aleatório
2. heurística de avaliação
3. Minimax com profundidade limitada
4. Alfa-Beta
5. Iterative Deepening com limite de tempo

### 12.4 Implementação

Detalhe as funções centrais:

- `choose_move`
- `evaluate_board`
- `score_window`
- `minimax`
- `alphabeta`
- `choose_move_iterative_deepening`

Explique também o papel do servidor em `server.py`, que isola a execução do agente em outro processo e impõe timeout rígido.

### 12.5 Experimentos

Apresente as comparações propostas:

- Minimax vs aleatório nas profundidades 2, 3, 4 e 5
- Alfa-Beta vs Minimax nas profundidades 2, 3, 4 e 5
- Iterative Deepening vs Alfa-Beta com limites de tempo de 1s e 2s
- partidas contra humano para análise qualitativa

### 12.6 Discussão

Comente os trade-offs entre profundidade, tempo e qualidade da decisão. Explique que aprofundar a busca nem sempre é útil se o limite de tempo impede completar a rodada.

### 12.7 Conclusão

Resuma qual técnica se mostrou mais equilibrada para o ambiente com tempo rígido e aponte possíveis melhorias futuras.

## 13. Experimentos sugeridos e métricas

Use esta seção como base para tabelas e figuras no relatório.

### 13.1 Minimax vs Aleatório

Para cada profundidade:

- taxa de vitória
- taxa de empate
- tempo médio por jogada
- média de nós visitados

Espera-se que a profundidade maior melhore a qualidade, mas aumente significativamente o custo.

### 13.2 Alfa-Beta vs Minimax

Para cada profundidade:

- taxa de vitória
- tempo médio por jogada
- média de nós visitados

Espera-se manter a qualidade e reduzir o número de nós visitados.

### 13.3 Iterative Deepening vs Alfa-Beta

Para cada limite de tempo:

- taxa de vitória
- tempo médio por jogada
- profundidade média atingida
- média de nós visitados

Espera-se que o agente entregue uma resposta melhor sob limitação rígida de tempo.

### 13.4 Partidas contra humano

Registre observações qualitativas como:

- força de bloqueio
- capacidade de criar ameaças
- preferência por centro
- erros recorrentes em táticas mais longas

### 13.5 Como registrar resultados

Para cada confronto, anote:

- método usado por cada lado
- profundidade ou tempo configurado
- número de partidas
- resultados finais
- observações relevantes sobre o comportamento do agente

## 14. Observações importantes sobre a execução

Esses pontos ajudam a interpretar corretamente o comportamento observado durante os testes.

### Timeout e fallback

- o agente tenta terminar a busca dentro do tempo configurado
- se o processo ultrapassar o limite rígido, o servidor interrompe a execução
- em caso de timeout ou falha, o servidor escolhe uma jogada válida aleatória como proteção

### Por que Iterative Deepening é importante

- ele garante que exista sempre uma melhor jogada conhecida até a última profundidade concluída
- isso é mais seguro do que depender apenas de uma busca profunda única
- é a técnica mais adequada para competição com tempo fixo por jogada

### Como interpretar a comparação entre profundidades

- profundidade maior normalmente melhora a qualidade da decisão
- porém, se o tempo não permitir completar a busca, a vantagem prática pode desaparecer
- por isso o relatório deve discutir custo e benefício, não apenas vitória ou derrota

## 15. Texto-base para introduzir o relatório

O trecho abaixo pode servir como rascunho para a introdução do texto final:

"Neste trabalho foi desenvolvido um agente de IA para o jogo Ligue-4 utilizando busca adversarial. A implementação foi construída de forma incremental, partindo de uma baseline aleatória, seguida por uma função heurística de avaliação, pela busca Minimax com profundidade limitada, pela poda Alfa-Beta e, por fim, por Iterative Deepening para adequação ao limite de tempo por jogada. A proposta permitiu comparar qualidade de decisão, número de nós expandidos e tempo médio por jogada em diferentes configurações, evidenciando o impacto das otimizações de busca em um ambiente de jogo competitivo."

## 16. Texto-base para a metodologia

Outro rascunho útil para o relatório:

"A heurística foi projetada para refletir características estratégicas relevantes do Connect Four, como valorização da coluna central, identificação de janelas com sequências abertas e penalização de ameaças do oponente. Sobre essa avaliação, foi implementado Minimax com profundidade limitada, posteriormente otimizado com poda Alfa-Beta. Para respeitar o limite rígido de tempo imposto pelo servidor, a versão final do agente utiliza Iterative Deepening, que explora sucessivamente profundidades crescentes e mantém a melhor jogada completamente avaliada antes do esgotamento do tempo."

Se você quiser, eu posso transformar essas seções em um esqueleto de LaTeX já com títulos, subtítulos e espaços para tabelas.
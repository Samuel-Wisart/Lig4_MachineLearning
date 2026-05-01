from typing import List, Tuple, Optional, Dict
import time
import math
import random

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2

# -----------------------------------------------------------------------------
# Utilidades de tabuleiro (PRONTAS)
# -----------------------------------------------------------------------------
def copy_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]

def valid_moves(board: List[List[int]]) -> List[int]:
    """Retorna as colunas ainda jogáveis (topo vazio)."""
    return [c for c in range(COLS) if board[0][c] == EMPTY]

def make_move(board: List[List[int]], col: int, player: int) -> Optional[List[List[int]]]:
    """Retorna um novo tabuleiro aplicando a gravidade na coluna col; None se inválido."""
    if col < 0 or col >= COLS or board[0][col] != EMPTY:
        return None
    nb = copy_board(board)
    for r in reversed(range(ROWS)):
        if nb[r][col] == EMPTY:
            nb[r][col] = player
            return nb
    return None

def winner(board: List[List[int]]) -> int:
    """0 se ninguém venceu; 1 ou 2 se há 4 em linha."""
    # Horizontais
    for r in range(ROWS):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return x
    # Verticais
    for c in range(COLS):
        for r in range(ROWS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return x
    # Diag ↘
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return x
    # Diag ↗
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                return x
    return 0

def is_full(board: List[List[int]]) -> bool:
    return all(board[0][c] != EMPTY for c in range(COLS))

def terminal(board: List[List[int]]) -> Tuple[bool, int]:
    """(é_terminal, vencedor) com vencedor=0 para empate/indefinido."""
    w = winner(board)
    if w != 0:
        return True, w
    if is_full(board):
        return True, 0
    return False, 0

def other(player: int) -> int:
    return P1 if player == P2 else P2

# -----------------------------------------------------------------------------
# HEURÍSTICA
# -----------------------------------------------------------------------------
# Variaveis de pontuação ajustadas por algoritmo genético (ver relatório).
WIN_SCORE = 100000
THREE_IN_A_ROW_SCORE = 108
TWO_IN_A_ROW_SCORE = 11
CENTER_COLUMN_SCORE = 5
OPP_THREE_PENALTY = 110
OPP_TWO_PENALTY = 11
FUTURE_THREE_FACTOR = 0.4025
FUTURE_TWO_FACTOR = 0.575

def score_window(
    window: List[int],
    player: int,
    playable_empties: Optional[int] = None,
    use_future: bool = True,
) -> int:
    """Avalia uma janela de 4 células do ponto de vista de `player`."""
    opponent = other(player)
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(EMPTY)

    # Janela bloqueada (peças dos dois jogadores) não vira 4 em linha para ninguém.
    if player_count > 0 and opponent_count > 0:
        return 0

    if playable_empties is None:
        playable_empties = empty_count

    if player_count == 4:
        return WIN_SCORE
    if opponent_count == 4:
        return -WIN_SCORE

    score = 0

    immediate = playable_empties >= 1
    future_three = int(THREE_IN_A_ROW_SCORE * FUTURE_THREE_FACTOR) if use_future else 0
    future_two = int(TWO_IN_A_ROW_SCORE * FUTURE_TWO_FACTOR) if use_future else 0
    future_opp_three = int(OPP_THREE_PENALTY * FUTURE_THREE_FACTOR) if use_future else 0
    future_opp_two = int(OPP_TWO_PENALTY * FUTURE_TWO_FACTOR) if use_future else 0

    if player_count == 3 and empty_count == 1:
        score += THREE_IN_A_ROW_SCORE if immediate else future_three
    elif player_count == 2 and empty_count == 2:
        score += TWO_IN_A_ROW_SCORE if immediate else future_two

    if opponent_count == 3 and empty_count == 1:
        score -= OPP_THREE_PENALTY if immediate else future_opp_three
    elif opponent_count == 2 and empty_count == 2:
        score -= OPP_TWO_PENALTY if immediate else future_opp_two

    return score

def is_playable_cell(board: List[List[int]], row: int, col: int) -> bool:
    """Retorna se uma célula vazia pode ser jogada agora (respeitando gravidade)."""
    return row == ROWS - 1 or board[row + 1][col] != EMPTY

def score_window_with_coords(
    board: List[List[int]],
    coords: List[Tuple[int, int]],
    player: int,
    use_future: bool = True,
) -> int:
    """Extrai uma janela por coordenadas e passa para score_window com noção de jogabilidade."""
    window = [board[r][c] for r, c in coords]
    playable_empties = 0
    for row, col in coords:
        if board[row][col] == EMPTY and is_playable_cell(board, row, col):
            playable_empties += 1
    return score_window(window, player, playable_empties, use_future=use_future)

def evaluate_board(
    board: List[List[int]],
    player: int,
    use_future: bool = True,
) -> int:
    """Calcula a qualidade do tabuleiro para `player`. Valores altos favorecem `player`."""
    is_terminal, winner_player = terminal(board)
    if is_terminal:
        if winner_player == player:
            return WIN_SCORE
        if winner_player == other(player):
            return -WIN_SCORE
        return 0

    score = 0

    # Preferência pela coluna central
    center_column = COLS // 2
    center_count = 0
    for row in range(ROWS):
        if board[row][center_column] == player:
            center_count += 1
    score += center_count * CENTER_COLUMN_SCORE

    # Janelas horizontais
    for row in range(ROWS):
        for col in range(COLS - 3):
            coords = [(row, col + offset) for offset in range(4)]
            score += score_window_with_coords(board, coords, player, use_future=use_future)

    # Janelas verticais
    for col in range(COLS):
        for row in range(ROWS - 3):
            coords = [(row + offset, col) for offset in range(4)]
            score += score_window_with_coords(board, coords, player, use_future=use_future)

    # Janelas diagonais descendentes
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            coords = [(row + offset, col + offset) for offset in range(4)]
            score += score_window_with_coords(board, coords, player, use_future=use_future)

    # Janelas diagonais ascendentes
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            coords = [(row - offset, col + offset) for offset in range(4)]
            score += score_window_with_coords(board, coords, player, use_future=use_future)

    return score

def ordered_moves(board: List[List[int]]) -> List[int]:
    """Ordena colunas por proximidade ao centro para melhorar a qualidade do Minimax."""
    center = COLS // 2
    legal = valid_moves(board)
    return sorted(legal, key=lambda col: abs(col - center))

def minimax(
    board: List[List[int]],
    depth: int,
    maximizing: bool,
    root_player: int,
    current_player: int,
    deadline: float,
    stats: Dict[str, int],
    use_future: bool,
) -> Tuple[int, Optional[int], bool]:
    """
    Retorna (score, best_move, completed).
    completed=False indica que o tempo foi estourado durante a busca.
    """
    if time.perf_counter() >= deadline:
        return 0, None, False

    stats["nodes"] = stats.get("nodes", 0) + 1

    is_terminal, _ = terminal(board)
    if depth == 0 or is_terminal:
        return evaluate_board(board, root_player, use_future=use_future), None, True

    legal = ordered_moves(board)
    if not legal:
        return evaluate_board(board, root_player, use_future=use_future), None, True

    if maximizing:
        best_score = -math.inf
        best_move = legal[0]
        for col in legal:
            child = make_move(board, col, current_player)
            if child is None:
                continue

            child_score, _, completed = minimax(
                child,
                depth - 1,
                False,
                root_player,
                other(current_player),
                deadline,
                stats,
                use_future,
            )
            if not completed:
                return 0, None, False

            if child_score > best_score:
                best_score = child_score
                best_move = col

        return int(best_score), best_move, True

    # Se minimizing
    best_score = math.inf
    best_move = legal[0]
    for col in legal:
        child = make_move(board, col, current_player)
        if child is None:
            continue

        child_score, _, completed = minimax(
            child,
            depth - 1,
            True,
            root_player,
            other(current_player),
            deadline,
            stats,
            use_future,
        )
        if not completed:
            return 0, None, False

        if child_score < best_score:
            best_score = child_score
            best_move = col

    return int(best_score), best_move, True

def alphabeta(
    board: List[List[int]],
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    root_player: int,
    current_player: int,
    deadline: float,
    stats: Dict[str, int],
    use_future: bool,
) -> Tuple[int, Optional[int], bool]:
    """
    Retorna (score, best_move, completed) usando poda Alfa-Beta.
    completed=False indica que o tempo foi estourado durante a busca.
    """
    if time.perf_counter() >= deadline:
        return 0, None, False

    stats["nodes"] = stats.get("nodes", 0) + 1

    is_terminal, _ = terminal(board)
    if depth == 0 or is_terminal:
        return evaluate_board(board, root_player, use_future=use_future), None, True

    legal = ordered_moves(board)
    if not legal:
        return evaluate_board(board, root_player, use_future=use_future), None, True

    if maximizing:
        best_score = -math.inf
        best_move = legal[0]
        for col in legal:
            child = make_move(board, col, current_player)
            if child is None:
                continue

            child_score, _, completed = alphabeta(
                child,
                depth - 1,
                alpha,
                beta,
                False,
                root_player,
                other(current_player),
                deadline,
                stats,
                use_future,
            )
            if not completed:
                return 0, None, False

            if child_score > best_score:
                best_score = child_score
                best_move = col

            alpha = max(alpha, best_score)
            if beta <= alpha:
                stats["prunes"] = stats.get("prunes", 0) + 1
                break

        return int(best_score), best_move, True

    best_score = math.inf
    best_move = legal[0]
    for col in legal:
        child = make_move(board, col, current_player)
        if child is None:
            continue

        child_score, _, completed = alphabeta(
            child,
            depth - 1,
            alpha,
            beta,
            True,
            root_player,
            other(current_player),
            deadline,
            stats,
            use_future,
        )
        if not completed:
            return 0, None, False

        if child_score < best_score:
            best_score = child_score
            best_move = col

        beta = min(beta, best_score)
        if beta <= alpha:
            stats["prunes"] = stats.get("prunes", 0) + 1
            break

    return int(best_score), best_move, True

# -----------------------------------------------------------------------------
# ÚNICO PONTO A SER IMPLEMENTADO PELOS ALUNOS
# -----------------------------------------------------------------------------
def choose_move_search(board: List[List[int]], turn: int, config: Dict, method: str) -> int:
    """
    Decide a coluna (0..6) para jogar agora com o método escolhido.

    method:
      - "minimax"
            - "alphabeta"
            - "iterative_deepening"
    """
    max_time_ms = int(config.get("max_time_ms"))
    max_depth = int(config.get("max_depth"))
    turn = int(turn)
    use_future = bool(config.get("use_future", True))
    print(
        f"AI choose_move called with method={method}, max_time_ms={max_time_ms}, "
        f"max_depth={max_depth}, player={turn}, use_future={use_future}"
    )

    legal = valid_moves(board)
    if not legal:
        # Sem jogadas: devolve 0 por convenção (servidor lida com isso)
        return 0

    if max_time_ms > 0:
        deadline = time.perf_counter() + (max_time_ms / 1000.0) * 0.80
    else:
        deadline = time.perf_counter() + 3600.0

    search_depth = max(1, max_depth)

    def resolve_move(candidate: Optional[int], completed: bool) -> int:
        if completed and candidate is not None and candidate in legal:
            return candidate
        return random.choice(legal)

    if method == "minimax":
        stats: Dict[str, int] = {"nodes": 0}
        score, best_move, completed = minimax(
            board=board,
            depth=search_depth,
            maximizing=True,
            root_player=turn,
            current_player=turn,
            deadline=deadline,
            stats=stats,
            use_future=use_future,
        )

        move = resolve_move(best_move, completed)

        print(
            "Minimax selected "
            f"col={move} score={score} nodes={stats['nodes']} completed={completed}"
        )
        return move

    if method == "iterative_deepening":
        best_move = None
        best_score = 0
        best_depth = 0
        nodes_total = 0
        prunes_total = 0

        depth = 1
        while time.perf_counter() < deadline:
            stats = {"nodes": 0, "prunes": 0}
            score, move_candidate, completed = alphabeta(
                board=board,
                depth=depth,
                alpha=-math.inf,
                beta=math.inf,
                maximizing=True,
                root_player=turn,
                current_player=turn,
                deadline=deadline,
                stats=stats,
                use_future=use_future,
            )

            nodes_total += stats["nodes"]
            prunes_total += stats["prunes"]

            if completed and move_candidate is not None and move_candidate in legal:
                best_move = move_candidate
                best_score = score
                best_depth = depth
                depth += 1
                continue

            break

        if best_move is None:
            best_move = random.choice(legal)

        print(
            "IterativeDeepening selected "
            f"col={best_move} score={best_score} depth_reached={best_depth} "
            f"nodes={nodes_total} prunes={prunes_total}"
        )
        return best_move

    stats = {"nodes": 0, "prunes": 0}
    score, best_move, completed = alphabeta(
        board=board,
        depth=search_depth,
        alpha=-math.inf,
        beta=math.inf,
        maximizing=True,
        root_player=turn,
        current_player=turn,
        deadline=deadline,
        stats=stats,
        use_future=use_future,
    )

    move = resolve_move(best_move, completed)

    print(
        "AlphaBeta selected "
        f"col={move} score={score} nodes={stats['nodes']} prunes={stats['prunes']} completed={completed}"
    )

    return move

def choose_move(board: List[List[int]], turn: int, config: Dict) -> int:
    """Modo padrão do aluno: Iterative Deepening com Alfa-Beta."""
    return choose_move_search(board, turn, config, method="iterative_deepening")

def choose_move_iterative_deepening(board: List[List[int]], turn: int, config: Dict) -> int:
    """IA com Iterative Deepening sobre Alfa-Beta, para uso principal e competição."""
    return choose_move_search(board, turn, config, method="iterative_deepening")

def choose_move_minimax(board: List[List[int]], turn: int, config: Dict) -> int:
    """IA com busca Minimax sem poda, para comparação."""
    return choose_move_search(board, turn, config, method="minimax")

def choose_move_alphabeta(board: List[List[int]], turn: int, config: Dict) -> int:
    """IA com busca Alfa-Beta, para comparação."""
    return choose_move_search(board, turn, config, method="alphabeta")

def choose_move_randomly(board: List[List[int]], turn: int, config: Dict) -> int:
    max_time_ms = int(config.get("max_time_ms"))
    max_depth = int(config.get("max_depth"))
    turn = int(turn)

    print(f"AI choose_move called with max_time_ms={max_time_ms}, max_depth={max_depth}, player={turn}")
    
    legal = valid_moves(board)

    if not legal:
        return 0

    return random.choice(legal)


def choose_move_infinity(board: List[List[int]], turn: int, config: Dict) -> int:
    """
    Decide a coluna (0..6) para jogar agora.

    Parâmetros:
      - board: matriz 6x7 com valores {0,1,2}
      - turn: 1 ou 2
      - config: {"max_time_ms": int, "max_depth": int}

    Retorna:
      - col: int (0..6)
    """
    max_time_ms = int(config.get("max_time_ms"))
    max_depth = int(config.get("max_depth"))
    turn = int(turn)

    print(f"AI choose_move called with max_time_ms={max_time_ms}, max_depth={max_depth}, player={turn}")
    
    legal = valid_moves(board)
    if not legal:
        # Sem jogadas: devolve 0 por convenção (servidor lida com isso)
        return 0

    # Loop infinito proposital para testar o timeout do servidor.
    while True:
        pass
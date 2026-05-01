#!/usr/bin/env python3
"""
Experimentos de comparação entre algoritmos de busca em Connect Four.
"""

import time
import random
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import search

# Configuração de experimentos
GAMES_PER_CONFIG = 5  # Reduzido para testes rápidos  
RANDOM_SEED_BASE = 42

class ExperimentResult:
    """Armazena resultados de um experimento."""
    def __init__(self, name: str):
        self.name = name
        self.games = []
        self.stats = {
            "minimax_wins": 0,
            "alphabeta_wins": 0,
            "random_wins": 0,
            "iterative_wins": 0,
            "draws": 0,
            "total_games": 0,
            "minimax_times": [],
            "alphabeta_times": [],
            "random_times": [],
            "iterative_times": [],
            "minimax_nodes": [],
            "alphabeta_nodes": [],
            "minimax_prunes": [],
            "alphabeta_prunes": [],
            "iterative_nodes": [],
            "iterative_prunes": [],
            "iterative_depths": [],
            "red_wins": 0,
            "yellow_wins": 0,
        }

def play_game(
    red_func,
    yellow_func,
    red_config: Dict,
    yellow_config: Dict,
    seed: int = None,
) -> Tuple[int, List[Dict]]:
    """
    Simula um jogo entre dois jogadores. Retorna (vencedor, log_de_eventos).
    vencedor: 0 (empate), 1 (vermelho), 2 (amarelo)
    """
    if seed is not None:
        random.seed(seed)
    
    board = [[0] * 7 for _ in range(6)]
    turn = 1  # 1 = vermelho, 2 = amarelo
    move_log = []
    
    while True:
        is_terminal, winner = search.terminal(board)
        if is_terminal:
            return winner, move_log
        
        # Escolhe função baseado no turno
        if turn == 1:
            func = red_func
            config = red_config
            player_name = "Vermelho"
        else:
            func = yellow_func
            config = yellow_config
            player_name = "Amarelo"
        
        # Captura logs da IA
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        t0 = time.perf_counter()
        try:
            col = func(board, turn, config)
        except Exception as e:
            sys.stdout = old_stdout
            print(f"Erro ao executar {player_name}: {e}")
            return 3 - turn, move_log
        
        t1 = time.perf_counter()
        log_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        elapsed_ms = int((t1 - t0) * 1000)
        
        # Parse log
        nodes = parse_nodes(log_output)
        prunes = parse_prunes(log_output)
        depth = parse_depth(log_output)
        
        move_log.append({
            "player": turn,
            "column": col,
            "time_ms": elapsed_ms,
            "nodes": nodes,
            "prunes": prunes,
            "depth": depth,
            "log": log_output,
        })
        
        # Aplica movimento
        new_board = search.make_move(board, col, turn)
        if new_board is None:
            # Movimento inválido, passa turno (não deveria acontecer)
            turn = 3 - turn
            continue
        
        board = new_board
        turn = 3 - turn

def is_full(board: List[List[int]]) -> bool:
    """Checa se o tabuleiro está cheio."""
    return all(board[0][c] != 0 for c in range(7))

def parse_nodes(log: str) -> int:
    """Extrai número de nós do log da IA."""
    match = re.search(r"nodes=(\d+)", log)
    return int(match.group(1)) if match else 0

def parse_prunes(log: str) -> int:
    """Extrai número de podas do log da IA."""
    match = re.search(r"prunes=(\d+)", log)
    return int(match.group(1)) if match else 0

def parse_depth(log: str) -> int:
    """Extrai profundidade atingida do log da IA."""
    match = re.search(r"depth_reached=(\d+)", log)
    return int(match.group(1)) if match else 0

def experiment_minimax_vs_random(result: ExperimentResult):
    """Minimax vs Aleatório em profundidades 2, 3, 4."""
    print("\n=== Experimento 1: Minimax vs Aleatório ===")
    
    for depth in [2, 3, 4]:
        # Reduz número de testes para profundidades maiores
        num_games = max(3, GAMES_PER_CONFIG // (depth - 1)) if depth > 3 else GAMES_PER_CONFIG
        print(f"  Profundidade {depth} ({num_games} jogos)...")
        minimax_wins = 0
        random_wins = 0
        draws = 0
        minimax_times = []
        random_times = []
        minimax_nodes_list = []
        random_times_list = []
        
        for game_num in range(num_games):
            seed = RANDOM_SEED_BASE + depth * 100 + game_num
            
            minimax_config = {"max_time_ms": 0, "max_depth": depth}
            random_config = {"max_time_ms": 0, "max_depth": 1}
            
            winner, log = play_game(
                search.choose_move_minimax,
                search.choose_move_randomly,
                minimax_config,
                random_config,
                seed=seed,
            )
            
            if winner == 1:
                minimax_wins += 1
            elif winner == 2:
                random_wins += 1
            else:
                draws += 1
            
            # Coleta tempos (aproximado)
            if log:
                for move in log:
                    if move["player"] == 1:
                        minimax_times.append(move["time_ms"])
                        minimax_nodes_list.append(move["nodes"])
                    else:
                        random_times.append(move["time_ms"])
        
        result.stats[f"minimax_vs_random_depth_{depth}"] = {
            "minimax_wins": minimax_wins,
            "random_wins": random_wins,
            "draws": draws,
            "minimax_avg_time": sum(minimax_times) / len(minimax_times) if minimax_times else 0,
            "random_avg_time": sum(random_times) / len(random_times) if random_times else 0,
            "minimax_avg_nodes": sum(minimax_nodes_list) / len(minimax_nodes_list) if minimax_nodes_list else 0,
        }
        
        print(f"    Minimax: {minimax_wins}W, Aleatório: {random_wins}W, Empates: {draws}")

def experiment_alphabeta_vs_minimax(result: ExperimentResult):
    """Alfa-Beta vs Minimax em profundidades 2, 3, 4."""
    print("\n=== Experimento 2: Alfa-Beta vs Minimax ===")
    
    for depth in [2, 3, 4]:
        # Reduz número de testes para profundidades maiores
        num_games = max(3, GAMES_PER_CONFIG // (depth - 1)) if depth > 3 else GAMES_PER_CONFIG
        print(f"  Profundidade {depth} ({num_games} jogos)...")
        alphabeta_wins = 0
        minimax_wins = 0
        draws = 0
        alphabeta_times = []
        minimax_times = []
        alphabeta_nodes_list = []
        minimax_nodes_list = []
        
        for game_num in range(num_games):
            seed = RANDOM_SEED_BASE + depth * 200 + game_num
            
            alphabeta_config = {"max_time_ms": 0, "max_depth": depth}
            minimax_config = {"max_time_ms": 0, "max_depth": depth}
            
            winner, log = play_game(
                search.choose_move_alphabeta,
                search.choose_move_minimax,
                alphabeta_config,
                minimax_config,
                seed=seed,
            )
            
            if winner == 1:
                alphabeta_wins += 1
            elif winner == 2:
                minimax_wins += 1
            else:
                draws += 1
            
            # Coleta tempos e nós
            if log:
                for move in log:
                    if move["player"] == 1:
                        alphabeta_times.append(move["time_ms"])
                        alphabeta_nodes_list.append(move["nodes"])
                    else:
                        minimax_times.append(move["time_ms"])
                        minimax_nodes_list.append(move["nodes"])
        
        result.stats[f"alphabeta_vs_minimax_depth_{depth}"] = {
            "alphabeta_wins": alphabeta_wins,
            "minimax_wins": minimax_wins,
            "draws": draws,
            "alphabeta_avg_time": sum(alphabeta_times) / len(alphabeta_times) if alphabeta_times else 0,
            "minimax_avg_time": sum(minimax_times) / len(minimax_times) if minimax_times else 0,
            "alphabeta_avg_nodes": sum(alphabeta_nodes_list) / len(alphabeta_nodes_list) if alphabeta_nodes_list else 0,
            "minimax_avg_nodes": sum(minimax_nodes_list) / len(minimax_nodes_list) if minimax_nodes_list else 0,
        }
        
        print(f"    Alfa-Beta: {alphabeta_wins}W, Minimax: {minimax_wins}W, Empates: {draws}")

def experiment_iterative_deepening_vs_alphabeta(result: ExperimentResult):
    """Iterative Deepening vs Alfa-Beta com limites de tempo 1s e 2s."""
    print("\n=== Experimento 3: Iterative Deepening vs Alfa-Beta ===")
    
    for time_limit_ms in [1000, 2000]:
        print(f"  Limite de tempo {time_limit_ms} ms (2 jogos)...")
        iterative_wins = 0
        alphabeta_wins = 0
        draws = 0
        iterative_times = []
        alphabeta_times = []
        iterative_nodes_list = []
        alphabeta_nodes_list = []
        iterative_depths_list = []
        
        for game_num in range(2):  # Reduzido para 2 jogos por tempo
            seed = RANDOM_SEED_BASE + time_limit_ms + game_num
            
            iterative_config = {"max_time_ms": time_limit_ms, "max_depth": 25}
            alphabeta_config = {"max_time_ms": time_limit_ms, "max_depth": 25}
            
            winner, log = play_game(
                search.choose_move_iterative_deepening,
                search.choose_move_alphabeta,
                iterative_config,
                alphabeta_config,
                seed=seed,
            )
            
            if winner == 1:
                iterative_wins += 1
            elif winner == 2:
                alphabeta_wins += 1
            else:
                draws += 1
            
            # Coleta tempos, nós e profundidade
            if log:
                for move in log:
                    if move["player"] == 1:
                        iterative_times.append(move["time_ms"])
                        iterative_nodes_list.append(move["nodes"])
                        iterative_depths_list.append(move["depth"])
                    else:
                        alphabeta_times.append(move["time_ms"])
                        alphabeta_nodes_list.append(move["nodes"])
        
        result.stats[f"iterative_vs_alphabeta_time_{time_limit_ms}"] = {
            "iterative_wins": iterative_wins,
            "alphabeta_wins": alphabeta_wins,
            "draws": draws,
            "iterative_avg_time": sum(iterative_times) / len(iterative_times) if iterative_times else 0,
            "alphabeta_avg_time": sum(alphabeta_times) / len(alphabeta_times) if alphabeta_times else 0,
            "iterative_avg_nodes": sum(iterative_nodes_list) / len(iterative_nodes_list) if iterative_nodes_list else 0,
            "alphabeta_avg_nodes": sum(alphabeta_nodes_list) / len(alphabeta_nodes_list) if alphabeta_nodes_list else 0,
            "iterative_avg_depth": sum(iterative_depths_list) / len(iterative_depths_list) if iterative_depths_list else 0,
        }
        
        print(f"    Iterative: {iterative_wins}W, Alfa-Beta: {alphabeta_wins}W, Empates: {draws}")

def generate_report(result: ExperimentResult, filename: str = "relatorio_experimentos.txt"):
    """Gera relatório em arquivo TXT."""
    print("\n=== Gerando relatório ===")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE EXPERIMENTOS - CONNECT FOUR\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("1. EXPERIMENTO: MINIMAX VS ALEATÓRIO\n")
        f.write("-" * 80 + "\n")
        for depth in [2, 3, 4]:
            key = f"minimax_vs_random_depth_{depth}"
            if key in result.stats:
                data = result.stats[key]
                total = data["minimax_wins"] + data["random_wins"] + data["draws"]
                minimax_pct = 100.0 * data["minimax_wins"] / total if total > 0 else 0
                random_pct = 100.0 * data["random_wins"] / total if total > 0 else 0
                
                f.write(f"\nProfundidade {depth}:\n")
                f.write(f"  Minimax vs Aleatório ({total} jogos):\n")
                f.write(f"    - Minimax: {data['minimax_wins']} vitórias ({minimax_pct:.1f}%)\n")
                f.write(f"    - Aleatório: {data['random_wins']} vitórias ({random_pct:.1f}%)\n")
                f.write(f"    - Empates: {data['draws']}\n")
                f.write(f"    - Tempo médio (Minimax): {data['minimax_avg_time']:.2f} ms\n")
                f.write(f"    - Tempo médio (Aleatório): {data['random_avg_time']:.2f} ms\n")
                f.write(f"    - Nós visitados médios (Minimax): {data['minimax_avg_nodes']:.0f}\n")
        
        f.write("\n\n2. EXPERIMENTO: ALFA-BETA VS MINIMAX\n")
        f.write("-" * 80 + "\n")
        for depth in [2, 3, 4]:
            key = f"alphabeta_vs_minimax_depth_{depth}"
            if key in result.stats:
                data = result.stats[key]
                total = data["alphabeta_wins"] + data["minimax_wins"] + data["draws"]
                alphabeta_pct = 100.0 * data["alphabeta_wins"] / total if total > 0 else 0
                minimax_pct = 100.0 * data["minimax_wins"] / total if total > 0 else 0
                
                f.write(f"\nProfundidade {depth}:\n")
                f.write(f"  Alfa-Beta vs Minimax ({total} jogos):\n")
                f.write(f"    - Alfa-Beta: {data['alphabeta_wins']} vitórias ({alphabeta_pct:.1f}%)\n")
                f.write(f"    - Minimax: {data['minimax_wins']} vitórias ({minimax_pct:.1f}%)\n")
                f.write(f"    - Empates: {data['draws']}\n")
                f.write(f"    - Tempo médio (Alfa-Beta): {data['alphabeta_avg_time']:.2f} ms\n")
                f.write(f"    - Tempo médio (Minimax): {data['minimax_avg_time']:.2f} ms\n")
                f.write(f"    - Nós visitados médios (Alfa-Beta): {data['alphabeta_avg_nodes']:.0f}\n")
                f.write(f"    - Nós visitados médios (Minimax): {data['minimax_avg_nodes']:.0f}\n")
                
                # Redução de nós (eficiência da poda)
                if data['minimax_avg_nodes'] > 0:
                    reduction = 100.0 * (1 - data['alphabeta_avg_nodes'] / data['minimax_avg_nodes'])
                    f.write(f"    - Redução de nós (Alfa-Beta): {reduction:.1f}%\n")
        
        f.write("\n\n3. EXPERIMENTO: ITERATIVE DEEPENING VS ALFA-BETA\n")
        f.write("-" * 80 + "\n")
        for time_limit_ms in [1000, 2000]:
            key = f"iterative_vs_alphabeta_time_{time_limit_ms}"
            if key in result.stats:
                data = result.stats[key]
                total = data["iterative_wins"] + data["alphabeta_wins"] + data["draws"]
                iterative_pct = 100.0 * data["iterative_wins"] / total if total > 0 else 0
                alphabeta_pct = 100.0 * data["alphabeta_wins"] / total if total > 0 else 0
                
                f.write(f"\nLimite de tempo {time_limit_ms} ms:\n")
                f.write(f"  Iterative Deepening vs Alfa-Beta ({total} jogos):\n")
                f.write(f"    - Iterative Deepening: {data['iterative_wins']} vitórias ({iterative_pct:.1f}%)\n")
                f.write(f"    - Alfa-Beta: {data['alphabeta_wins']} vitórias ({alphabeta_pct:.1f}%)\n")
                f.write(f"    - Empates: {data['draws']}\n")
                f.write(f"    - Tempo médio (Iterative): {data['iterative_avg_time']:.2f} ms\n")
                f.write(f"    - Tempo médio (Alfa-Beta): {data['alphabeta_avg_time']:.2f} ms\n")
                f.write(f"    - Profundidade média atingida (Iterative): {data['iterative_avg_depth']:.1f}\n")
                f.write(f"    - Nós visitados médios (Iterative): {data['iterative_avg_nodes']:.0f}\n")
                f.write(f"    - Nós visitados médios (Alfa-Beta): {data['alphabeta_avg_nodes']:.0f}\n")
        
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("FIM DO RELATÓRIO\n")
        f.write("=" * 80 + "\n")
    
    print(f"Relatório salvo em '{filename}'")

def generate_graphs(result: ExperimentResult):
    """Gera gráficos dos resultados."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Matplotlib não instalado. Pulando geração de gráficos.")
        return
    
    print("=== Gerando gráficos ===")
    
    # Gráfico 1: Taxa de vitória vs Profundidade (Minimax vs Aleatório)
    fig, ax = plt.subplots(figsize=(10, 6))
    depths = []
    minimax_wins = []
    random_wins = []
    
    for depth in [2, 3, 4]:
        key = f"minimax_vs_random_depth_{depth}"
        if key in result.stats:
            data = result.stats[key]
            total = data["minimax_wins"] + data["random_wins"] + data["draws"]
            depths.append(depth)
            minimax_wins.append(100.0 * data["minimax_wins"] / total if total > 0 else 0)
            random_wins.append(100.0 * data["random_wins"] / total if total > 0 else 0)
    
    ax.plot(depths, minimax_wins, marker='o', label='Minimax', linewidth=2, markersize=8)
    ax.plot(depths, random_wins, marker='s', label='Aleatório', linewidth=2, markersize=8)
    ax.set_xlabel('Profundidade', fontsize=12)
    ax.set_ylabel('Taxa de Vitória (%)', fontsize=12)
    ax.set_title('Minimax vs Aleatório - Taxa de Vitória por Profundidade', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(depths)
    plt.tight_layout()
    plt.savefig('grafico_minimax_vs_random.png', dpi=150)
    print("Gráfico salvo: grafico_minimax_vs_random.png")
    plt.close()
    
    # Gráfico 2: Comparação de tempo e nós (Alfa-Beta vs Minimax)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    depths = []
    alphabeta_times = []
    minimax_times = []
    alphabeta_nodes = []
    minimax_nodes = []
    
    for depth in [2, 3, 4]:
        key = f"alphabeta_vs_minimax_depth_{depth}"
        if key in result.stats:
            data = result.stats[key]
            depths.append(depth)
            alphabeta_times.append(data['alphabeta_avg_time'])
            minimax_times.append(data['minimax_avg_time'])
            alphabeta_nodes.append(data['alphabeta_avg_nodes'])
            minimax_nodes.append(data['minimax_avg_nodes'])
    
    ax1.plot(depths, alphabeta_times, marker='o', label='Alfa-Beta', linewidth=2, markersize=8)
    ax1.plot(depths, minimax_times, marker='s', label='Minimax', linewidth=2, markersize=8)
    ax1.set_xlabel('Profundidade', fontsize=11)
    ax1.set_ylabel('Tempo Médio (ms)', fontsize=11)
    ax1.set_title('Tempo Médio por Profundidade', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(depths)
    
    ax2.plot(depths, alphabeta_nodes, marker='o', label='Alfa-Beta', linewidth=2, markersize=8)
    ax2.plot(depths, minimax_nodes, marker='s', label='Minimax', linewidth=2, markersize=8)
    ax2.set_xlabel('Profundidade', fontsize=11)
    ax2.set_ylabel('Nós Visitados (média)', fontsize=11)
    ax2.set_title('Nós Visitados por Profundidade', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(depths)
    
    plt.tight_layout()
    plt.savefig('grafico_alfabeta_vs_minimax.png', dpi=150)
    print("Gráfico salvo: grafico_alfabeta_vs_minimax.png")
    plt.close()
    
    # Gráfico 3: Iterative Deepening vs Alfa-Beta
    fig, ax = plt.subplots(figsize=(10, 6))
    time_limits = [1000, 2000]
    iterative_wins = []
    alphabeta_wins = []
    
    for time_limit_ms in time_limits:
        key = f"iterative_vs_alphabeta_time_{time_limit_ms}"
        if key in result.stats:
            data = result.stats[key]
            total = data["iterative_wins"] + data["alphabeta_wins"] + data["draws"]
            iterative_wins.append(100.0 * data["iterative_wins"] / total if total > 0 else 0)
            alphabeta_wins.append(100.0 * data["alphabeta_wins"] / total if total > 0 else 0)
    
    x = np.arange(len(time_limits))
    width = 0.35
    
    ax.bar(x - width/2, iterative_wins, width, label='Iterative Deepening', alpha=0.8)
    ax.bar(x + width/2, alphabeta_wins, width, label='Alfa-Beta', alpha=0.8)
    ax.set_xlabel('Limite de Tempo', fontsize=12)
    ax.set_ylabel('Taxa de Vitória (%)', fontsize=12)
    ax.set_title('Iterative Deepening vs Alfa-Beta - Taxa de Vitória por Limite de Tempo', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{t} ms' for t in time_limits])
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('grafico_iterative_vs_alphabeta.png', dpi=150)
    print("Gráfico salvo: grafico_iterative_vs_alphabeta.png")
    plt.close()

def main():
    """Executa todos os experimentos."""
    print("Iniciando experimentos de Connect Four...")
    
    result = ExperimentResult("Connect Four Experiments")
    
    # Executa experimentos
    experiment_minimax_vs_random(result)
    experiment_alphabeta_vs_minimax(result)
    experiment_iterative_deepening_vs_alphabeta(result)
    
    # Gera relatório e gráficos
    generate_report(result)
    generate_graphs(result)
    
    print("\n✓ Experimentos finalizados com sucesso!")

if __name__ == "__main__":
    main()

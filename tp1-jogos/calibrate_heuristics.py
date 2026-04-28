from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import search


@dataclass(frozen=True)
class WeightProfile:
    name: str
    win_score: int
    three_in_a_row_score: int
    two_in_a_row_score: int
    center_column_score: int
    opp_three_penalty: int
    opp_two_penalty: int
    future_three_factor: float
    future_two_factor: float

    def to_config(self, max_time_ms: int, max_depth: int) -> Dict[str, object]:
        return {
            "max_time_ms": max_time_ms,
            "max_depth": max_depth,
            "use_future": True,
            "WIN_SCORE": self.win_score,
            "THREE_IN_A_ROW_SCORE": self.three_in_a_row_score,
            "TWO_IN_A_ROW_SCORE": self.two_in_a_row_score,
            "CENTER_COLUMN_SCORE": self.center_column_score,
            "OPP_THREE_PENALTY": self.opp_three_penalty,
            "OPP_TWO_PENALTY": self.opp_two_penalty,
            "FUTURE_THREE_FACTOR": self.future_three_factor,
            "FUTURE_TWO_FACTOR": self.future_two_factor,
        }


BASE_PROFILE = WeightProfile(
    name="base",
    win_score=100000,
    three_in_a_row_score=100,
    two_in_a_row_score=10,
    center_column_score=6,
    opp_three_penalty=120,
    opp_two_penalty=12,
    future_three_factor=0.35,
    future_two_factor=0.50,
)


def new_board() -> List[List[int]]:
    return [[0 for _ in range(search.COLS)] for _ in range(search.ROWS)]


def profile_from_scales(
    name: str,
    offense_scale: float = 1.0,
    center_scale: float = 1.0,
    defense_scale: float = 1.0,
    future_scale: float = 1.0,
) -> WeightProfile:
    return WeightProfile(
        name=name,
        win_score=BASE_PROFILE.win_score,
        three_in_a_row_score=max(1, int(round(BASE_PROFILE.three_in_a_row_score * offense_scale))),
        two_in_a_row_score=max(1, int(round(BASE_PROFILE.two_in_a_row_score * offense_scale))),
        center_column_score=max(0, int(round(BASE_PROFILE.center_column_score * center_scale))),
        opp_three_penalty=max(1, int(round(BASE_PROFILE.opp_three_penalty * defense_scale))),
        opp_two_penalty=max(1, int(round(BASE_PROFILE.opp_two_penalty * defense_scale))),
        future_three_factor=max(0.0, BASE_PROFILE.future_three_factor * future_scale),
        future_two_factor=max(0.0, BASE_PROFILE.future_two_factor * future_scale),
    )


def play_game(
    red: WeightProfile,
    yellow: WeightProfile,
    max_time_ms: int,
    max_depth: int,
    seed: int,
) -> Dict[str, object]:
    board = new_board()
    turn = search.P1
    move_count = 0
    elapsed_red = 0.0
    elapsed_yellow = 0.0

    random.seed(seed)

    while True:
        terminal_state, winner = search.terminal(board)
        if terminal_state:
            break

        current_profile = red if turn == search.P1 else yellow
        config = current_profile.to_config(max_time_ms=max_time_ms, max_depth=max_depth)

        started = time.perf_counter()
        col = search.choose_move_iterative_deepening(board, turn, config)
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        if turn == search.P1:
            elapsed_red += elapsed_ms
        else:
            elapsed_yellow += elapsed_ms

        board = search.make_move(board, col, turn)
        if board is None:
            raise RuntimeError(f"Jogada inválida retornada pela IA: coluna {col}")

        move_count += 1
        turn = search.other(turn)

    return {
        "winner": winner,
        "moves": move_count,
        "elapsed_red_ms": elapsed_red,
        "elapsed_yellow_ms": elapsed_yellow,
    }


def matchup_score(result: Dict[str, object], red: WeightProfile, yellow: WeightProfile) -> Dict[str, float]:
    winner = int(result["winner"])
    if winner == search.P1:
        red_points = 1.0
        yellow_points = 0.0
    elif winner == search.P2:
        red_points = 0.0
        yellow_points = 1.0
    else:
        red_points = 0.5
        yellow_points = 0.5

    return {
        red.name: red_points,
        yellow.name: yellow_points,
        f"{red.name}_time_ms": float(result["elapsed_red_ms"]),
        f"{yellow.name}_time_ms": float(result["elapsed_yellow_ms"]),
    }


def compare_profiles(
    candidate: WeightProfile,
    reference: WeightProfile,
    max_time_ms: int,
    max_depth: int,
    games_per_side: int,
    seed_base: int,
) -> Dict[str, float]:
    total_candidate_points = 0.0
    total_reference_points = 0.0
    total_candidate_time = 0.0
    total_reference_time = 0.0

    orientations = [(candidate, reference), (reference, candidate)]
    for orientation_index, (red, yellow) in enumerate(orientations):
        for game_index in range(games_per_side):
            seed = seed_base + orientation_index * 100 + game_index
            result = play_game(red, yellow, max_time_ms=max_time_ms, max_depth=max_depth, seed=seed)
            score = matchup_score(result, red, yellow)
            total_candidate_points += score.get(candidate.name, 0.0)
            total_reference_points += score.get(reference.name, 0.0)
            total_candidate_time += score.get(f"{candidate.name}_time_ms", 0.0)
            total_reference_time += score.get(f"{reference.name}_time_ms", 0.0)

    return {
        "candidate_points": total_candidate_points,
        "reference_points": total_reference_points,
        "point_delta": total_candidate_points - total_reference_points,
        "candidate_time_ms": total_candidate_time,
        "reference_time_ms": total_reference_time,
    }


def tune_for_time(
    max_time_ms: int,
    max_depth: int,
    games_per_side: int,
) -> Tuple[WeightProfile, List[Dict[str, object]]]:
    current = BASE_PROFILE
    history: List[Dict[str, object]] = []

    dimensions = [
        ("offense", "offense_scale", [0.92, 1.08]),
        ("center", "center_scale", [0.90, 1.10]),
        ("defense", "defense_scale", [0.92, 1.08]),
        ("future", "future_scale", [0.85, 1.15]),
    ]

    scales = {"offense_scale": 1.0, "center_scale": 1.0, "defense_scale": 1.0, "future_scale": 1.0}

    for dimension_name, scale_key, candidates in dimensions:
        best_candidate = current
        best_score = -math.inf
        best_detail: Dict[str, object] | None = None

        for value in candidates:
            trial_scales = dict(scales)
            trial_scales[scale_key] = value
            trial = profile_from_scales(
                name=f"{dimension_name}={value:.2f}",
                offense_scale=trial_scales["offense_scale"],
                center_scale=trial_scales["center_scale"],
                defense_scale=trial_scales["defense_scale"],
                future_scale=trial_scales["future_scale"],
            )

            result = compare_profiles(
                candidate=trial,
                reference=current,
                max_time_ms=max_time_ms,
                max_depth=max_depth,
                games_per_side=games_per_side,
                seed_base=7000 + max_time_ms + int(value * 1000),
            )

            detail = {
                "dimension": dimension_name,
                "candidate": trial,
                "reference": current,
                **result,
            }
            history.append(detail)

            score = result["point_delta"]
            if score > best_score:
                best_score = score
                best_candidate = trial
                best_detail = detail
            elif score == best_score and best_detail is not None:
                if result["candidate_time_ms"] < best_detail["candidate_time_ms"]:
                    best_candidate = trial
                    best_detail = detail

        current = best_candidate
        scales = {
            "offense_scale": current.three_in_a_row_score / BASE_PROFILE.three_in_a_row_score,
            "center_scale": current.center_column_score / BASE_PROFILE.center_column_score if BASE_PROFILE.center_column_score else 1.0,
            "defense_scale": current.opp_three_penalty / BASE_PROFILE.opp_three_penalty,
            "future_scale": current.future_three_factor / BASE_PROFILE.future_three_factor if BASE_PROFILE.future_three_factor else 1.0,
        }

    return current, history


def format_profile(profile: WeightProfile) -> str:
    return (
        f"WIN={profile.win_score}, THREE={profile.three_in_a_row_score}, TWO={profile.two_in_a_row_score}, "
        f"CENTER={profile.center_column_score}, OPP_THREE={profile.opp_three_penalty}, OPP_TWO={profile.opp_two_penalty}, "
        f"FUTURE_THREE={profile.future_three_factor:.3f}, FUTURE_TWO={profile.future_two_factor:.3f}"
    )


def history_to_markdown(history: List[Dict[str, object]]) -> str:
    lines = [
        "| Etapa | Candidato | Delta pontos | Pontos candidato | Pontos referência | Tempo candidato (ms) | Tempo referência (ms) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for item in history:
        candidate: WeightProfile = item["candidate"]
        lines.append(
            f"| {item['dimension']} | {candidate.name} | {item['point_delta']:.1f} | {item['candidate_points']:.1f} | {item['reference_points']:.1f} | {item['candidate_time_ms']:.1f} | {item['reference_time_ms']:.1f} |"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ajusta pesos da heurística por self-play com iterative deepening.")
    parser.add_argument("--games-per-side", type=int, default=1, help="Quantidade de jogos por lado para cada comparação.")
    parser.add_argument("--max-depth", type=int, default=6, help="Profundidade máxima do iterative deepening.")
    args = parser.parse_args()

    results: Dict[int, Dict[str, object]] = {}

    for max_time_ms in (1000, 2000):
        print(f"\n=== Ajustando para {max_time_ms} ms ===")
        tuned_profile, history = tune_for_time(
            max_time_ms=max_time_ms,
            max_depth=args.max_depth,
            games_per_side=args.games_per_side,
        )
        results[max_time_ms] = {
            "profile": tuned_profile,
            "history": history,
        }

        print(f"Melhor perfil ({max_time_ms} ms): {format_profile(tuned_profile)}")
        print(history_to_markdown(history))

    print("\n=== Resumo final ===")
    for max_time_ms, data in results.items():
        profile: WeightProfile = data["profile"]
        print(f"{max_time_ms} ms -> {format_profile(profile)}")


if __name__ == "__main__":
    main()
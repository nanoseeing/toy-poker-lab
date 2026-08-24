"""Command-line interface for toy poker experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from toy_poker.experiments.comparison import compare_runs
from toy_poker.experiments.benchmark import benchmark_experiment
from toy_poker.experiments.config import ExperimentConfig
from toy_poker.experiments.runner import rerender_artifact, run_experiment
from toy_poker.games import list_games


def main() -> None:
    parser = argparse.ArgumentParser(prog="toy-poker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list-games", help="List registered games")
    run_parser = subparsers.add_parser("run", help="Run an experiment TOML")
    run_parser.add_argument("config", type=Path)
    run_parser.add_argument("--output-dir", type=Path)
    report_parser = subparsers.add_parser("report", help="Re-render a saved run")
    report_parser.add_argument("run_dir", type=Path)
    compare_parser = subparsers.add_parser("compare", help="Compare completed runs")
    compare_parser.add_argument("run_dirs", type=Path, nargs="+")
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Benchmark solver execution without writing artifacts"
    )
    benchmark_parser.add_argument("config", type=Path)
    benchmark_parser.add_argument("--iterations", type=int)
    benchmark_parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    if args.command == "list-games":
        for plugin in list_games():
            print(f"{plugin.metadata.game_id}: {plugin.metadata.title}")
    elif args.command == "run":
        result = run_experiment(
            ExperimentConfig.from_toml(args.config), output_directory=args.output_dir
        )
        print(f"Report: {(result.directory / 'report.html').resolve()}")
        print(json.dumps(result.analysis["summary"], indent=2, ensure_ascii=False))
    elif args.command == "report":
        rerender_artifact(args.run_dir)
        print(f"Report: {(args.run_dir / 'report.html').resolve()}")
    elif args.command == "compare":
        print(json.dumps(compare_runs(args.run_dirs), indent=2, ensure_ascii=False))
    elif args.command == "benchmark":
        print(
            json.dumps(
                benchmark_experiment(
                    args.config, iterations=args.iterations, repeat=args.repeat
                ),
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()

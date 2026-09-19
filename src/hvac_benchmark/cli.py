"""`hvac-benchmark` command-line entry point."""

from __future__ import annotations

import argparse
import dataclasses

from .config import DEFAULT_CONFIG, BenchmarkConfig
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="hvac-benchmark", description=__doc__)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--cache-dir", default="data_cache")
    parser.add_argument("--skip-download", action="store_true", help="reuse an existing cache only")
    parser.add_argument("--no-ablations", action="store_true", help="skip the uniform-prior/lambda ablations")
    parser.add_argument(
        "--no-troubleshooting", action="store_true", help="skip the troubleshooting-against-a-blueprint mode"
    )
    parser.add_argument(
        "--quick", action="store_true", help="smoke-test settings: fewer seeds and one noise level"
    )
    parser.add_argument("--seeds", type=int, default=None, help="override number of seeds")
    parser.add_argument(
        "--workers", type=int, default=1,
        help="parallel worker processes (one unit = one topology/relation; each loads its own Brick ontology)",
    )
    parser.add_argument(
        "--no-checkpoint", action="store_true",
        help="do not write/read per-unit checkpoints under <results-dir>/checkpoints",
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="ignore existing checkpoints and recompute (use after code changes that affect trial outcomes)",
    )
    args = parser.parse_args()

    config = DEFAULT_CONFIG
    if args.quick:
        config = dataclasses.replace(config, n_seeds=3, noise_levels=(0.0, 0.05))
    if args.seeds is not None:
        config = dataclasses.replace(config, n_seeds=args.seeds)

    run_pipeline(
        results_dir=args.results_dir,
        cache_dir=args.cache_dir,
        config=config,
        skip_download=args.skip_download,
        run_ablations_flag=not args.no_ablations,
        run_troubleshooting_flag=not args.no_troubleshooting,
        workers=args.workers,
        checkpoint=not args.no_checkpoint,
        fresh=args.fresh,
    )


if __name__ == "__main__":
    main()

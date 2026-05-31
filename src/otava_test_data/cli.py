#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Command-line interface for generating Otava test data.

Usage:
    otava-gen --help
    otava-gen generate --output-dir ./test_data
    otava-gen generate --lengths 50 500 --seed 42
"""

import argparse
import sys
import json
from pathlib import Path

from otava_test_data.generators.combiner import CombinationGenerator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="otava-gen",
        description="Generate test data for Apache Otava change point detection",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate test data CSV files",
    )
    gen_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./otava_test_data",
        help="Output directory for CSV files (default: ./otava_test_data)",
    )
    gen_parser.add_argument(
        "--lengths", "-l",
        type=int,
        nargs="+",
        default=[50, 500],
        help="Time series lengths to generate (default: 50 500)",
    )
    gen_parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    gen_parser.add_argument(
        "--noise-levels",
        type=float,
        nargs="+",
        default=[0.0, 2.0, 5.0, 10.0],
        help="Noise sigma levels to apply (default: 0 2 5 10)",
    )
    gen_parser.add_argument(
        "--no-combinations",
        action="store_true",
        help="Skip generating pairwise combinations",
    )
    gen_parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only generate manifest JSON, no CSV files",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available generators",
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show information about a generator",
    )
    info_parser.add_argument(
        "generator",
        type=str,
        help="Generator name",
    )

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    """Execute the generate command."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating test data in {output_dir}")
    print(f"  Lengths: {args.lengths}")
    print(f"  Seed: {args.seed}")
    print(f"  Noise levels: {args.noise_levels}")
    print(f"  Include combinations: {not args.no_combinations}")

    generator = CombinationGenerator(lengths=args.lengths, seed=args.seed)

    all_series = generator.generate_all_test_cases(
        include_combinations=not args.no_combinations,
        noise_levels=args.noise_levels,
    )

    manifest = []

    for i, ts in enumerate(all_series):
        # Create safe filename
        safe_name = (
            ts.generator_name
            .replace("(", "_")
            .replace(")", "")
            .replace(", ", "_")
            .replace(" ", "_")
            .replace("+", "_plus_")
        )[:50]

        filename = f"{i:04d}_{safe_name}_L{len(ts)}.csv"

        entry = {
            "id": i,
            "filename": filename,
            "generator": ts.generator_name,
            "length": len(ts),
            "n_change_points": len(ts.change_points),
            "change_point_indices": ts.get_change_point_indices(),
            "change_point_types": [cp.change_type for cp in ts.change_points],
            "parameters": ts.parameters,
        }
        manifest.append(entry)

        if not args.manifest_only:
            filepath = output_dir / filename
            ts.to_csv(str(filepath))

            if (i + 1) % 50 == 0:
                print(f"  Generated {i + 1} files...")

    # Write manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Write summary
    summary = {
        "total_files": len(manifest),
        "lengths": args.lengths,
        "seed": args.seed,
        "noise_levels": args.noise_levels,
        "generators_used": list(set(e["generator"].split("(")[0] for e in manifest)),
        "total_change_points": sum(e["n_change_points"] for e in manifest),
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nGenerated {len(manifest)} test cases")
    print(f"  Manifest: {manifest_path}")
    print(f"  Summary: {summary_path}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Execute the list command."""
    generator = CombinationGenerator()
    blocks = generator.generate_basic_blocks()

    print("Available generators:")
    print()
    for name, func in blocks:
        doc = func.__doc__ or "No description"
        first_line = doc.strip().split("\n")[0]
        print(f"  {name:25s} {first_line}")

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Execute the info command."""
    generator = CombinationGenerator()
    blocks = dict(generator.generate_basic_blocks())

    if args.generator not in blocks:
        print(f"Unknown generator: {args.generator}")
        print(f"Available: {', '.join(blocks.keys())}")
        return 1

    func = blocks[args.generator]
    print(f"Generator: {args.generator}")
    print()
    print(func.__doc__ or "No documentation available")

    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "generate":
            return cmd_generate(args)
        elif args.command == "list":
            return cmd_list(args)
        elif args.command == "info":
            return cmd_info(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())

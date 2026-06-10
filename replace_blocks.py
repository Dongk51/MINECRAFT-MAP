#!/usr/bin/env python3
"""
replace_blocks.py — Minecraft Java Edition block replacement CLI

Usage examples:
  python replace_blocks.py path/to/world minecraft:stone minecraft:diamond_block
  python replace_blocks.py path/to/world stone diamond_block --dimension nether
  python replace_blocks.py path/to/world minecraft:grass_block minecraft:dirt --dry-run
  python replace_blocks.py path/to/world "minecraft:oak_log[axis=y]" "minecraft:spruce_log[axis=y]"
"""

import argparse
import logging
import sys

from block_replacer.core import DIMENSIONS, replace_blocks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replace_blocks",
        description="Replace every occurrence of one block with another inside a Minecraft Java Edition world.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "world_path",
        help="Path to the Minecraft world folder (contains level.dat).",
    )
    parser.add_argument(
        "source",
        help=(
            "Block to replace.  Accepts 'stone', 'minecraft:stone', "
            "or 'minecraft:oak_log[axis=y]' (include blockstate properties in quotes)."
        ),
    )
    parser.add_argument(
        "target",
        help="Block to place instead (same format as source).",
    )
    parser.add_argument(
        "--dimension",
        "-d",
        default="overworld",
        choices=list(DIMENSIONS.keys()),
        help="Dimension to process (default: overworld).",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Count replacements without writing any changes to disk.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output (errors are still shown).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    if not args.quiet:
        print(f"World   : {args.world_path}")
        print(f"Source  : {args.source}")
        print(f"Target  : {args.target}")
        print(f"Dim     : {args.dimension}")
        if args.dry_run:
            print("Mode    : dry-run (no changes will be saved)")
        print()

    try:
        count = replace_blocks(
            world_path=args.world_path,
            source_block=args.source,
            target_block=args.target,
            dimension=args.dimension,
            dry_run=args.dry_run,
            progress=not args.quiet,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    verb = "Would replace" if args.dry_run else "Replaced"
    print(f"\n{verb} {count:,} block(s).")
    if args.dry_run:
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate_terrain.py — Minecraft Java Edition terrain generation CLI

Subcommands
-----------
  flat    Fill every column to a fixed height with a single block.
  hills   Apply Perlin-noise height map to create rolling hills.

Region (optional for both subcommands)
-----------
  --x1/--z1/--x2/--z2  Block coordinates defining the working area.
  If omitted, the entire world (all existing chunks) is processed.

Usage examples
--------------
  python generate_terrain.py path/to/world flat --block minecraft:grass_block --height 64
  python generate_terrain.py path/to/world flat --block stone --height 32 --x1 -100 --z1 -100 --x2 100 --z2 100
  python generate_terrain.py path/to/world hills --block minecraft:stone
  python generate_terrain.py path/to/world hills --block dirt --base-height 60 --amplitude 25 --scale 80
  python generate_terrain.py path/to/world hills --block minecraft:grass_block --dry-run
"""

import argparse
import logging
import sys
import traceback

from terrain_generator import DIMENSIONS


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _add_common_args(p: argparse.ArgumentParser) -> None:
    """Args shared by all subcommands."""
    p.add_argument("world_path", help="Path to the Minecraft world folder (contains level.dat).")
    p.add_argument(
        "--dimension", "-d",
        default="overworld",
        choices=list(DIMENSIONS.keys()),
        help="Dimension to target (default: overworld).",
    )
    p.add_argument(
        "--x1", type=int, default=None, metavar="X",
        help="Region west boundary (block coordinate). Requires --z1 --x2 --z2.",
    )
    p.add_argument("--z1", type=int, default=None, metavar="Z", help="Region north boundary.")
    p.add_argument("--x2", type=int, default=None, metavar="X", help="Region east boundary.")
    p.add_argument("--z2", type=int, default=None, metavar="Z", help="Region south boundary.")
    p.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Count blocks without writing any changes to disk.",
    )
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output.")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="generate_terrain",
        description="Generate or reshape terrain in a Minecraft Java Edition world.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = root.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # -- flat --
    flat_p = sub.add_parser(
        "flat",
        help="Fill columns to a fixed height with one block.",
        description="Fill every column in the target area from world min_y up to HEIGHT with BLOCK.",
    )
    _add_common_args(flat_p)
    flat_p.add_argument(
        "--block", "-b", required=True,
        help="Block to fill with, e.g. 'minecraft:grass_block' or 'stone'.",
    )
    flat_p.add_argument(
        "--height", type=int, required=True,
        help="World y to fill up to (exclusive), e.g. 64.",
    )

    # -- hills --
    hills_p = sub.add_parser(
        "hills",
        help="Apply Perlin-noise height map to create rolling hills.",
        description=(
            "Use 2D Perlin noise to derive a per-column height and fill each column "
            "from world min_y to that height with BLOCK."
        ),
    )
    _add_common_args(hills_p)
    hills_p.add_argument(
        "--block", "-b", required=True,
        help="Block to fill each column with.",
    )
    hills_p.add_argument(
        "--base-height", type=int, default=64,
        help="Median terrain height in world y coordinates (default: 64).",
    )
    hills_p.add_argument(
        "--amplitude", type=float, default=20.0,
        help="Max height deviation from base in blocks (default: 20).",
    )
    hills_p.add_argument(
        "--scale", type=float, default=100.0,
        help="Horizontal zoom of the noise — larger = smoother hills (default: 100).",
    )

    return root


# ---------------------------------------------------------------------------
# Region validation helpers
# ---------------------------------------------------------------------------

def _parse_region(args) -> "tuple[int, int, int, int] | None":
    coords = (args.x1, args.z1, args.x2, args.z2)
    if all(c is None for c in coords):
        return None
    if any(c is None for c in coords):
        print("Error: --x1 --z1 --x2 --z2 must all be provided together.", file=sys.stderr)
        sys.exit(1)
    return (args.x1, args.z1, args.x2, args.z2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    region = _parse_region(args)

    if not args.quiet:
        print(f"World     : {args.world_path}")
        print(f"Command   : {args.command}")
        print(f"Dimension : {args.dimension}")
        if region:
            print(f"Region    : x={args.x1}..{args.x2}  z={args.z1}..{args.z2}")
        else:
            print("Region    : entire world")
        if args.dry_run:
            print("Mode      : dry-run (no changes saved)")
        print()

    try:
        if args.command == "flat":
            if not args.quiet:
                print(f"Block     : {args.block}")
                print(f"Height    : {args.height}")
                print()
            from terrain_generator.flat import generate_flat
            count = generate_flat(
                world_path=args.world_path,
                block_str=args.block,
                height=args.height,
                region=region,
                dimension=args.dimension,
                dry_run=args.dry_run,
                progress=not args.quiet,
            )

        elif args.command == "hills":
            if not args.quiet:
                print(f"Block     : {args.block}")
                print(f"Base height: {args.base_height}")
                print(f"Amplitude : {args.amplitude}")
                print(f"Scale     : {args.scale}")
                print()
            from terrain_generator.hills import generate_hills
            count = generate_hills(
                world_path=args.world_path,
                block_str=args.block,
                base_height=args.base_height,
                amplitude=args.amplitude,
                scale=args.scale,
                region=region,
                dimension=args.dimension,
                dry_run=args.dry_run,
                progress=not args.quiet,
            )

    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    verb = "Would write" if args.dry_run else "Wrote"
    print(f"\n{verb} {count:,} block(s).")
    if args.dry_run:
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()

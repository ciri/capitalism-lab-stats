#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_summary(path: Path) -> dict:
	return json.loads(path.read_text(encoding="utf-8"))


def compare_pair(left: dict, right: dict) -> dict:
	left_name  = left["save_file"]
	right_name = right["save_file"]
	left_world = left["world_snapshot"]
	right_world = right["world_snapshot"]
	return {
		"left": left_name,
		"right": right_name,
		"size_mb_delta": round(right_world["size_mb"] - left_world["size_mb"], 3),
		"entropy_delta": round(right_world["entropy"] - left_world["entropy"], 6),
		"zero_ratio_delta": round(right_world["zero_ratio"] - left_world["zero_ratio"], 6),
		"same_scenario": left.get("scenario") == right.get("scenario"),
	}


def build_report(summary_paths: list[Path]) -> dict:
	summaries = [load_summary(path) for path in summary_paths]
	pairs     = []
	for left_idx in range(len(summaries)):
		for right_idx in range(left_idx + 1, len(summaries)):
			pairs.append(compare_pair(summaries[left_idx], summaries[right_idx]))
	return {
		"summary_files": [path.name for path in summary_paths],
		"pairwise_comparison": pairs,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Compare logical save summary JSON files.")
	parser.add_argument("-i", "--inputs", nargs="+", required=True, help="Input summary JSON paths")
	parser.add_argument("-o", "--output", required=True, help="Output comparison JSON path")
	args = parser.parse_args()

	input_paths = [Path(item) for item in args.inputs]
	for path in input_paths:
		if not path.exists():
			raise FileNotFoundError(f"Summary file not found: {path}")

	report   = build_report(input_paths)
	out_path = Path(args.output)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote summary comparison: {out_path}")


if __name__ == "__main__":
	main()

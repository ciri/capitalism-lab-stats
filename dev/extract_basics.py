#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path


def longest_common_prefix(buffers: list[bytes]) -> int:
	if not buffers:
		return 0
	min_len = min(len(buf) for buf in buffers)
	for idx in range(min_len):
		value = buffers[0][idx]
		if any(buf[idx] != value for buf in buffers[1:]):
			return idx
	return min_len


def find_ascii_runs(buf: bytes, min_run: int = 6) -> list[dict[str, int | str]]:
	runs = []
	start = None
	for idx, byte in enumerate(buf):
		printable = 32 <= byte <= 126
		if printable and start is None:
			start = idx
		elif not printable and start is not None:
			if idx - start >= min_run:
				text = buf[start:idx].decode("ascii", errors="ignore")
				runs.append({"offset": start, "length": idx - start, "text": text})
			start = None
	if start is not None and len(buf) - start >= min_run:
		text = buf[start:].decode("ascii", errors="ignore")
		runs.append({"offset": start, "length": len(buf) - start, "text": text})
	return runs


def find_diff_ranges(buffers: dict[str, bytes]) -> list[dict[str, int]]:
	if len(buffers) < 2:
		return []
	min_len = min(len(buf) for buf in buffers.values())
	ranges = []
	in_range = False
	range_start = 0
	for idx in range(min_len):
		values = {buf[idx] for buf in buffers.values()}
		is_diff = len(values) > 1
		if is_diff and not in_range:
			in_range = True
			range_start = idx
		elif not is_diff and in_range:
			ranges.append({"start": range_start, "end": idx - 1, "length": idx - range_start})
			in_range = False
	if in_range:
		ranges.append({"start": range_start, "end": min_len - 1, "length": min_len - range_start})
	return ranges


def parse_u32_header(buf: bytes, count: int = 16) -> list[int]:
	values = []
	for idx in range(count):
		offset = idx * 4
		chunk  = buf[offset:offset + 4]
		if len(chunk) < 4:
			break
		values.append(int.from_bytes(chunk, "little", signed=False))
	return values


def build_report(data_dir: Path) -> dict:
	save_paths = sorted(data_dir.glob("*.SAV"))
	if not save_paths:
		raise FileNotFoundError(f"No .SAV files found in {data_dir}")

	buffers = {path.name: path.read_bytes() for path in save_paths}
	prefix  = longest_common_prefix(list(buffers.values()))
	diffs   = find_diff_ranges(buffers)

	report = {
		"saves": [],
		"all_files": {
			"longest_common_prefix": prefix,
			"diff_range_count": len(diffs),
			"largest_diff_ranges": sorted(diffs, key=lambda item: item["length"], reverse=True)[:12],
		},
	}

	for name, buf in buffers.items():
		entry = {
			"file": name,
			"size_bytes": len(buf),
			"header_u32": parse_u32_header(buf),
			"top_ascii_runs": sorted(find_ascii_runs(buf), key=lambda item: item["length"], reverse=True)[:12],
		}
		report["saves"].append(entry)

	for left, right in combinations(sorted(buffers), 2):
		left_buf  = buffers[left]
		right_buf = buffers[right]
		limit     = min(len(left_buf), len(right_buf))
		delta     = sum(1 for idx in range(limit) if left_buf[idx] != right_buf[idx])
		report.setdefault("pairwise", []).append(
			{
				"left": left,
				"right": right,
				"compared_bytes": limit,
				"different_bytes": delta,
				"difference_ratio": round(delta / limit, 6),
			}
		)

	return report


def main() -> None:
	parser = argparse.ArgumentParser(description="Extract baseline sections from Capitalism Lab save files.")
	parser.add_argument("--data-dir", default="data/saves", help="Directory containing .SAV files")
	parser.add_argument("--out", default="dev/out/baseline_report.json", help="Output JSON report path")
	args = parser.parse_args()

	data_dir = Path(args.data_dir)
	out_path = Path(args.out)
	out_path.parent.mkdir(parents=True, exist_ok=True)

	report = build_report(data_dir)
	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote baseline report: {out_path}")


if __name__ == "__main__":
	main()

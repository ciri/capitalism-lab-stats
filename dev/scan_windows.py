#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def record_bytes(buf: bytes, start: int, stride: int, limit: int) -> list[bytes]:
	records = []
	for rec_idx in range(limit):
		left  = start + rec_idx * stride
		right = left + stride
		if right > len(buf):
			break
		records.append(buf[left:right])
	return records


def average_record_delta(a_records: list[bytes], b_records: list[bytes]) -> float:
	count = min(len(a_records), len(b_records))
	if count == 0:
		return 1.0
	acc = 0.0
	for idx in range(count):
		a = a_records[idx]
		b = b_records[idx]
		if len(a) != len(b) or len(a) == 0:
			continue
		diff = sum(1 for x, y in zip(a, b) if x != y)
		acc += diff / len(a)
	return round(acc / count, 6)


def scan_windows(
	save_paths: list[Path],
	stride_min: int,
	stride_max: int,
	stride_step: int,
	start_min: int,
	start_max: int,
	start_step: int,
	sample_records: int,
	top_n: int,
) -> dict:
	buffers = {path.name: path.read_bytes() for path in save_paths}
	min_len = min(len(buf) for buf in buffers.values())

	results = []
	for stride in range(stride_min, stride_max + 1, stride_step):
		derived_start_max = max(0, min_len - stride * sample_records)
		effective_max     = min(start_max, derived_start_max)
		for start in range(start_min, effective_max + 1, start_step):
			window_records = {
				name: record_bytes(buf, start, stride, sample_records)
				for name, buf in buffers.items()
			}
			pairs      = []
			pair_names = sorted(window_records)
			for left_idx in range(len(pair_names)):
				for right_idx in range(left_idx + 1, len(pair_names)):
					left_name  = pair_names[left_idx]
					right_name = pair_names[right_idx]
					delta      = average_record_delta(window_records[left_name], window_records[right_name])
					pairs.append(delta)
			if not pairs:
				continue
			results.append(
				{
					"start": start,
					"stride": stride,
					"avg_cross_save_record_delta": round(sum(pairs) / len(pairs), 6),
					"pair_deltas": pairs,
					"record_count": min(len(records) for records in window_records.values()),
				}
			)

	best = sorted(results, key=lambda item: item["avg_cross_save_record_delta"])[:top_n]
	return {
		"parameters": {
			"stride_min": stride_min,
			"stride_max": stride_max,
			"stride_step": stride_step,
			"start_min": start_min,
			"start_max": start_max,
			"start_step": start_step,
			"sample_records": sample_records,
			"top_n": top_n,
		},
		"save_files": sorted(buffers),
		"best_windows": best,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Scan start/stride windows for coherent fixed-record regions.")
	parser.add_argument("--data-dir", default="data/saves", help="Directory containing .SAV files")
	parser.add_argument("--out", default="dev/out/window_scan.json", help="Output JSON path")
	parser.add_argument("--stride-min", type=int, default=752)
	parser.add_argument("--stride-max", type=int, default=768)
	parser.add_argument("--stride-step", type=int, default=4)
	parser.add_argument("--start-min", type=int, default=65536, help="Minimum byte offset for window starts")
	parser.add_argument("--start-max", type=int, default=2097152, help="Maximum byte offset for window starts")
	parser.add_argument("--start-step", type=int, default=4096)
	parser.add_argument("--sample-records", type=int, default=64)
	parser.add_argument("--top-n", type=int, default=40)
	args = parser.parse_args()

	saves = sorted(Path(args.data_dir).glob("*.SAV"))
	if not saves:
		raise FileNotFoundError(f"No .SAV files found in {args.data_dir}")

	report   = scan_windows(
		saves,
		args.stride_min,
		args.stride_max,
		args.stride_step,
		args.start_min,
		args.start_max,
		args.start_step,
		args.sample_records,
		args.top_n,
	)
	out_path = Path(args.out)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote window scan report: {out_path}")


if __name__ == "__main__":
	main()

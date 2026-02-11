#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def stride_score(buf: bytes, stride: int, sample_records: int = 1200) -> float:
	if stride <= 0:
		return 1.0
	record_count = min(len(buf) // stride, sample_records)
	if record_count < 3:
		return 1.0

	acc = 0
	cnt = 0
	for idx in range(record_count - 1):
		a = buf[idx * stride:(idx + 1) * stride]
		b = buf[(idx + 1) * stride:(idx + 2) * stride]
		if len(a) != stride or len(b) != stride:
			continue
		matches = sum(1 for x, y in zip(a, b) if x == y)
		acc    += matches / stride
		cnt    += 1
	if cnt == 0:
		return 1.0
	return round(acc / cnt, 6)


def scan_file(path: Path, start: int, stop: int, step: int) -> dict:
	buf = path.read_bytes()
	candidates = []
	for stride in range(start, stop + 1, step):
		score = stride_score(buf, stride)
		candidates.append({"stride": stride, "adjacent_similarity": score, "records": len(buf) // stride})

	best = sorted(candidates, key=lambda item: item["adjacent_similarity"])[:15]
	return {
		"file": path.name,
		"size_bytes": len(buf),
		"best_candidates": best,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Scan possible fixed-size record strides in save files.")
	parser.add_argument("--data-dir", default="data/saves", help="Directory with .SAV files")
	parser.add_argument("--out", default="dev/out/stride_candidates.json", help="Output JSON path")
	parser.add_argument("--start", type=int, default=32, help="Stride scan start")
	parser.add_argument("--stop", type=int, default=768, help="Stride scan stop")
	parser.add_argument("--step", type=int, default=4, help="Stride scan step")
	args = parser.parse_args()

	data_dir = Path(args.data_dir)
	out_path = Path(args.out)
	out_path.parent.mkdir(parents=True, exist_ok=True)

	saves = sorted(data_dir.glob("*.SAV"))
	if not saves:
		raise FileNotFoundError(f"No .SAV files found in {data_dir}")

	report = {
		"parameters": {
			"start": args.start,
			"stop": args.stop,
			"step": args.step,
		},
		"results": [scan_file(path, args.start, args.stop, args.step) for path in saves],
	}

	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote stride scan report: {out_path}")


if __name__ == "__main__":
	main()

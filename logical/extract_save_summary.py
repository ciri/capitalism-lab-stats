#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def printable_runs(buf: bytes, min_run: int = 6) -> list[str]:
	runs  = []
	start = None
	for idx, byte in enumerate(buf):
		printable = 32 <= byte <= 126
		if printable and start is None:
			start = idx
		elif not printable and start is not None:
			length = idx - start
			if length >= min_run:
				runs.append(buf[start:idx].decode("ascii", errors="ignore"))
			start = None
	if start is not None:
		length = len(buf) - start
		if length >= min_run:
			runs.append(buf[start:].decode("ascii", errors="ignore"))
	return runs


def byte_histogram(buf: bytes) -> list[int]:
	hist = [0] * 256
	for byte in buf:
		hist[byte] += 1
	return hist


def entropy_from_hist(hist: list[int], total: int) -> float:
	if total == 0:
		return 0.0
	acc = 0.0
	for freq in hist:
		if freq == 0:
			continue
		p    = freq / total
		acc -= p * math.log2(p)
	return round(acc, 6)


def classify_data_density(entropy: float, zero_ratio: float) -> str:
	if zero_ratio > 0.30:
		return "sparse"
	if entropy >= 7.60:
		return "high_activity"
	if entropy >= 6.20:
		return "medium_activity"
	return "low_activity"


def find_source_save_path(strings: list[str]) -> str | None:
	for text in strings:
		if "Capitalism Lab" in text and text.upper().endswith(".SAV"):
			return text
	return None


def infer_scenario_label(path: Path) -> str:
	name = path.stem.upper()
	if name.startswith("SPIK_"):
		return "Spike challenge series"
	return "Unknown scenario"


def summarize_save(path: Path) -> dict:
	buf          = path.read_bytes()
	hist         = byte_histogram(buf)
	strings      = printable_runs(buf)
	file_size_mb = round(len(buf) / (1024 * 1024), 3)
	zero_ratio   = round(hist[0] / len(buf), 6) if len(buf) else 0.0
	entropy      = entropy_from_hist(hist, len(buf))

	source_path = find_source_save_path(strings)
	firm_names  = []

	return {
		"save_file": path.name,
		"scenario": infer_scenario_label(path),
		"source_path": source_path,
		"game": "Capitalism Lab",
		"world_snapshot": {
			"size_mb": file_size_mb,
			"data_density": classify_data_density(entropy, zero_ratio),
			"entropy": entropy,
			"zero_ratio": zero_ratio,
		},
		"companies": {
			"main_company_name": "Unknown (not directly stored in detected text)",
			"estimated_company_count": "Unknown",
		},
		"firms": {
			"firm_names_detected": firm_names,
			"stores": "Unknown (requires deeper struct decoding)",
			"factories": "Unknown (requires deeper struct decoding)",
		},
		"quality_notes": [
			"This summary is designed for human readability and avoids raw offset-level details.",
			"Detailed firm/store decoding requires further struct inference from binary regions.",
		],
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate a logical, human-readable summary from one .SAV file.")
	parser.add_argument("-i", "--input", required=True, help="Input .SAV path")
	parser.add_argument("-o", "--output", required=True, help="Output JSON path")
	args = parser.parse_args()

	in_path  = Path(args.input)
	out_path = Path(args.output)
	if not in_path.exists():
		raise FileNotFoundError(f"Input save file not found: {in_path}")

	summary = summarize_save(in_path)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
	print(f"Wrote logical save summary: {out_path}")


if __name__ == "__main__":
	main()

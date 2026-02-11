#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import struct
from collections import defaultdict
from pathlib import Path


def get_records(buf: bytes, start: int, stride: int, limit: int) -> list[bytes]:
	records = []
	for idx in range(limit):
		left  = start + idx * stride
		right = left + stride
		if right > len(buf):
			break
		records.append(buf[left:right])
	return records


def u32_at(record: bytes, offset: int) -> int:
	chunk = record[offset:offset + 4]
	if len(chunk) < 4:
		return 0
	return int.from_bytes(chunk, "little", signed=False)


def f32_at(record: bytes, offset: int) -> float:
	chunk = record[offset:offset + 4]
	if len(chunk) < 4:
		return 0.0
	return struct.unpack("<f", chunk)[0]


def shannon_entropy(values: list[int]) -> float:
	if not values:
		return 0.0
	tally = defaultdict(int)
	for value in values:
		tally[value] += 1
	total = len(values)
	acc   = 0.0
	for freq in tally.values():
		p    = freq / total
		acc -= p * math.log2(p)
	return round(acc, 6)


def classify_u32(values: list[int]) -> tuple[str, float]:
	if not values:
		return "empty", 0.0
	unique_values = set(values)
	if len(unique_values) <= 1:
		return "constant", 1.0
	if all(values[idx] <= values[idx + 1] for idx in range(len(values) - 1)):
		return "monotonic_non_decreasing", 0.8
	if len(unique_values) <= max(8, len(values) // 16):
		return "low_cardinality", 0.7
	return "volatile", 0.6


def classify_f32(values: list[float]) -> tuple[str, float]:
	if not values:
		return "empty", 0.0
	finite_values = [value for value in values if math.isfinite(value)]
	if not finite_values:
		return "non_finite", 0.9
	zeros = sum(1 for value in finite_values if value == 0.0)
	if zeros == len(finite_values):
		return "all_zero", 1.0
	abs_values = [abs(value) for value in finite_values]
	very_large = sum(1 for value in abs_values if value > 1e20)
	very_small = sum(1 for value in abs_values if 0.0 < value < 1e-30)
	if very_large > len(finite_values) * 0.5:
		return "improbable_float_range", 0.8
	if very_small > len(finite_values) * 0.5:
		return "near_zero_dense", 0.7
	return "plausible_float", 0.6


def analyze_file(path: Path, start: int, stride: int, records: int) -> dict:
	buf          = path.read_bytes()
	record_bytes = get_records(buf, start, stride, records)
	if not record_bytes:
		return {"file": path.name, "record_count": 0, "fields": []}

	field_u32_values = defaultdict(list)
	field_f32_values = defaultdict(list)
	for rec in record_bytes:
		for offset in range(0, stride - 3, 4):
			field_u32_values[offset].append(u32_at(rec, offset))
			field_f32_values[offset].append(f32_at(rec, offset))

	fields = []
	for offset in sorted(field_u32_values):
		u32_values       = field_u32_values[offset]
		f32_values       = field_f32_values[offset]
		u32_class, u32_conf = classify_u32(u32_values)
		f32_class, f32_conf = classify_f32(f32_values)
		entry = {
			"offset": offset,
			"u32": {
				"classification": u32_class,
				"confidence": u32_conf,
				"unique_count": len(set(u32_values)),
				"min": min(u32_values),
				"max": max(u32_values),
				"entropy": shannon_entropy(u32_values),
			},
			"f32": {
				"classification": f32_class,
				"confidence": f32_conf,
				"finite_ratio": round(sum(1 for value in f32_values if math.isfinite(value)) / len(f32_values), 6),
				"sample_min": min(f32_values),
				"sample_max": max(f32_values),
			},
		}
		fields.append(entry)

	return {
		"file": path.name,
		"record_count": len(record_bytes),
		"fields": fields,
	}


def summarize_cross_file(results: list[dict]) -> dict:
	if not results:
		return {}
	by_offset_u32 = defaultdict(list)
	by_offset_f32 = defaultdict(list)
	for result in results:
		for field in result.get("fields", []):
			by_offset_u32[field["offset"]].append(field["u32"]["classification"])
			by_offset_f32[field["offset"]].append(field["f32"]["classification"])

	summary = []
	for offset in sorted(by_offset_u32):
		u32_classes = by_offset_u32[offset]
		f32_classes = by_offset_f32[offset]
		u32_tally   = defaultdict(int)
		f32_tally   = defaultdict(int)
		for cls in u32_classes:
			u32_tally[cls] += 1
		for cls in f32_classes:
			f32_tally[cls] += 1
		summary.append(
			{
				"offset": offset,
				"u32_class_tally": dict(sorted(u32_tally.items())),
				"f32_class_tally": dict(sorted(f32_tally.items())),
				"u32_all_same": len(set(u32_classes)) == 1,
				"f32_all_same": len(set(f32_classes)) == 1,
			}
		)
	return {"offset_summary": summary}


def main() -> None:
	parser = argparse.ArgumentParser(description="Classify u32/f32 field behavior inside candidate fixed-size records.")
	parser.add_argument("--data-dir", default="data/saves", help="Directory containing .SAV files")
	parser.add_argument("--out", default="dev/out/field_classification.json", help="Output JSON path")
	parser.add_argument("--start", type=int, default=65536, help="Byte start for candidate record region")
	parser.add_argument("--stride", type=int, default=768, help="Candidate record stride")
	parser.add_argument("--records", type=int, default=512, help="Number of records to sample")
	args = parser.parse_args()

	saves = sorted(Path(args.data_dir).glob("*.SAV"))
	if not saves:
		raise FileNotFoundError(f"No .SAV files found in {args.data_dir}")

	results = [analyze_file(path, args.start, args.stride, args.records) for path in saves]
	report  = {
		"parameters": {
			"start": args.start,
			"stride": args.stride,
			"records": args.records,
		},
		"files": results,
		"cross_file": summarize_cross_file(results),
	}

	out_path = Path(args.out)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote field classification report: {out_path}")


if __name__ == "__main__":
	main()

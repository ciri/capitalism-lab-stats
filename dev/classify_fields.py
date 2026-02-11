#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def classify_offset(values: list[int]) -> str:
	if not values:
		return "empty"
	unique_values = set(values)
	if len(unique_values) <= 1:
		return "constant"
	if all(values[idx] <= values[idx + 1] for idx in range(len(values) - 1)):
		return "monotonic_non_decreasing"
	if len(unique_values) <= max(8, len(values) // 16):
		return "low_cardinality"
	return "volatile"


def analyze_file(path: Path, start: int, stride: int, records: int) -> dict:
	buf          = path.read_bytes()
	record_bytes = get_records(buf, start, stride, records)
	if not record_bytes:
		return {"file": path.name, "record_count": 0, "fields": []}

	field_values = defaultdict(list)
	for rec in record_bytes:
		for offset in range(0, stride - 3, 4):
			field_values[offset].append(u32_at(rec, offset))

	fields = []
	for offset in sorted(field_values):
		values      = field_values[offset]
		classification = classify_offset(values)
		entry = {
			"offset": offset,
			"classification": classification,
			"unique_count": len(set(values)),
			"min": min(values),
			"max": max(values),
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
	by_offset = defaultdict(list)
	for result in results:
		for field in result.get("fields", []):
			by_offset[field["offset"]].append(field["classification"])

	summary = []
	for offset in sorted(by_offset):
		classes = by_offset[offset]
		tally   = defaultdict(int)
		for cls in classes:
			tally[cls] += 1
		summary.append(
			{
				"offset": offset,
				"class_tally": dict(sorted(tally.items())),
				"all_same": len(set(classes)) == 1,
			}
		)
	return {"offset_summary": summary}


def main() -> None:
	parser = argparse.ArgumentParser(description="Classify u32 field behavior inside candidate fixed-size records.")
	parser.add_argument("--data-dir", default="data/saves", help="Directory containing .SAV files")
	parser.add_argument("--out", default="dev/out/field_classification.json", help="Output JSON path")
	parser.add_argument("--start", type=int, default=0, help="Byte start for candidate record region")
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

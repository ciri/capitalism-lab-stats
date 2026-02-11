#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def parse_u32_words(buf: bytes, count: int = 16) -> list[dict[str, int]]:
	words = []
	for idx in range(count):
		offset = idx * 4
		chunk  = buf[offset:offset + 4]
		if len(chunk) < 4:
			break
		value = int.from_bytes(chunk, "little", signed=False)
		words.append({"offset": offset, "value": value})
	return words


def find_ascii_runs(buf: bytes, min_run: int = 6, top_n: int = 25) -> list[dict[str, int | str]]:
	runs  = []
	start = None
	for idx, byte in enumerate(buf):
		printable = 32 <= byte <= 126
		if printable and start is None:
			start = idx
		elif not printable and start is not None:
			length = idx - start
			if length >= min_run:
				text = buf[start:idx].decode("ascii", errors="ignore")
				runs.append({"offset": start, "length": length, "text": text})
			start = None
	if start is not None:
		length = len(buf) - start
		if length >= min_run:
			text = buf[start:].decode("ascii", errors="ignore")
			runs.append({"offset": start, "length": length, "text": text})
	return sorted(runs, key=lambda item: item["length"], reverse=True)[:top_n]


def byte_histogram(buf: bytes) -> list[int]:
	hist = [0] * 256
	for byte in buf:
		hist[byte] += 1
	return hist


def shannon_entropy_from_hist(hist: list[int], total: int) -> float:
	if total == 0:
		return 0.0
	acc = 0.0
	for freq in hist:
		if freq == 0:
			continue
		p    = freq / total
		acc -= p * math.log2(p)
	return round(acc, 6)


def chunk_entropy(buf: bytes, chunk_size: int = 65536, top_n: int = 16) -> dict:
	chunks = []
	for start in range(0, len(buf), chunk_size):
		end   = min(len(buf), start + chunk_size)
		part  = buf[start:end]
		hist  = byte_histogram(part)
		entry = {
			"start": start,
			"end": end - 1,
			"length": len(part),
			"entropy": shannon_entropy_from_hist(hist, len(part)),
			"zero_ratio": round(hist[0] / len(part), 6) if part else 0.0,
		}
		chunks.append(entry)
	return {
		"chunk_size": chunk_size,
		"top_entropy_chunks": sorted(chunks, key=lambda item: item["entropy"], reverse=True)[:top_n],
		"lowest_entropy_chunks": sorted(chunks, key=lambda item: item["entropy"])[:top_n],
	}


def decode_save(path: Path) -> dict:
	buf        = path.read_bytes()
	hist       = byte_histogram(buf)
	non_zero   = len(buf) - hist[0]
	ascii_runs = find_ascii_runs(buf)

	report = {
		"file": {
			"name": path.name,
			"path": str(path),
			"size_bytes": len(buf),
		},
		"header": {
			"u32_words": parse_u32_words(buf),
			"first_32_bytes_hex": buf[:32].hex(),
		},
		"distribution": {
			"zero_bytes": hist[0],
			"non_zero_bytes": non_zero,
			"zero_ratio": round(hist[0] / len(buf), 6) if buf else 0.0,
			"overall_entropy": shannon_entropy_from_hist(hist, len(buf)),
		},
		"ascii": {
			"top_runs": ascii_runs,
			"has_windows_save_path": any("Capitalism Lab" in run["text"] for run in ascii_runs),
		},
		"regions": chunk_entropy(buf),
	}
	return report


def main() -> None:
	parser = argparse.ArgumentParser(description="Human-readable single-save extractor for Capitalism Lab .SAV files.")
	parser.add_argument("-i", "--input", required=True, help="Input .SAV path")
	parser.add_argument("-o", "--output", required=True, help="Output JSON path")
	args = parser.parse_args()

	in_path  = Path(args.input)
	out_path = Path(args.output)
	if not in_path.exists():
		raise FileNotFoundError(f"Input save file not found: {in_path}")

	report = decode_save(in_path)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(f"Wrote save profile: {out_path}")


if __name__ == "__main__":
	main()

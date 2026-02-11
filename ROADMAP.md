# Save Decoding Roadmap

## Current baseline

- Added single-save extractor CLI:
	- `python alogicla/xyz.py -i <input.SAV> -o <output.json>`
- Produced human-readable outputs for each current save in `alogicla/out/`.

## Next steps

1. Add a comparer script that diffs two output JSON profiles and reports meaningful changes.
2. Add candidate record slicing (`start`, `stride`) to the single-save output format.
3. Add per-offset u32/f32 heuristic tags for likely ids, counters, and rate-like fields.
4. Add a stable CSV/table exporter for candidate firm-record rows.

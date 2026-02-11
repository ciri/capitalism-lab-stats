# /dev extraction scripts

This folder now contains basic, repeatable extraction scripts for initial save-file reversing:

- `extract_basics.py`
	- file size + first header words
	- common-prefix detection across saves
	- differing-byte range map across saves
	- ascii-run extraction for quick metadata anchors
- `scan_stride_candidates.py`
	- brute-force stride scan to prioritize fixed-record-size hypotheses
	- reports strides with lowest adjacent-record similarity

Outputs are written into `dev/out/` as JSON and are intended to feed `ROADMAP.md` updates.

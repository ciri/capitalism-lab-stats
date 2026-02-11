# /dev extraction scripts

This folder contains repeatable extraction scripts for save-file reversing.

- `extract_basics.py`
	- file size + first header words
	- common-prefix detection across saves
	- differing-byte range map across saves
	- ascii-run extraction for quick metadata anchors
- `scan_stride_candidates.py`
	- brute-force stride scan to prioritize fixed-record-size hypotheses
	- reports strides with lowest adjacent-record similarity
- `scan_windows.py`
	- bounded start/stride scan in a focused stride band (`752..768` by default)
	- defaults now skip early header-heavy bytes (`--start-min 65536`)
	- scores windows by cross-save record-level byte delta
- `classify_fields.py`
	- u32 + f32 per-offset behavior classifier
	- emits class confidence and u32 entropy
	- summarizes per-file and cross-file classification consistency

Outputs are written into `dev/out/` as JSON and should feed `ROADMAP.md` updates.

# Save Decoding Roadmap

## Dataset organization

- Save files are organized under `data/saves/`:
	- `SPIK_001.SAV`
	- `SPIK_002.SAV`
	- `SPIK_003.SAV`
- The current source manual snapshot is stored at `data/manuals/ORIGINAL_MANUAL.md`.

## Extraction status (current)

### 1) Global header + fixed metadata anchors

Status: **partially extracted**

What is confirmed:

- Byte range `0x0000-0x0003` is constant `0x00000000` across all saves.
- Byte range `0x0004-0x0007` decodes to little-endian `5416` (`0x00001528`) across all saves.
- A file-path ascii string starts at byte `0x0008` in at least `SPIK_001.SAV` and `SPIK_002.SAV`, e.g.
	- `C:\Users\enric\Documents\My Games\Capitalism Lab\SAVE\SPIK_001.SAV`
	- `C:\Users\enric\Documents\My Games\Capitalism Lab\SAVE\SPIK_002.SAV`
- Longest common prefix across all three saves is **69 bytes**.

### 2) Cross-save delta map (which sections change)

Status: **baseline extracted**

What is confirmed:

- We can consistently segment shared-length regions into equal vs different ranges.
- Current scan identifies **138 diff ranges** across the shared byte domain.
- Largest currently observed diff blocks:
	- `0x221D44-0x24C09D` (length 172,570)
	- `0x008AF6-0x0315AA` (length 166,613)
	- `0x0E66DA-0x10B3FA` (length 150,689)
	- `0x0C25FE-0x0E66D8` (length 147,851)
	- `0x05956C-0x07D389` (length 146,990)

Interpretation:

- Save state is heavily data-dense and scenario-dependent.
- We now have candidate high-entropy/high-variance zones to prioritize for struct slicing.

### 3) Pairwise file divergence

Status: **extracted**

What is confirmed:

- `SPIK_001` vs `SPIK_002`: 2,457,454 / 2,495,704 bytes differ (98.4674%).
- `SPIK_001` vs `SPIK_003`: 6,350,100 / 6,403,917 bytes differ (99.1596%).
- `SPIK_002` vs `SPIK_003`: 2,457,505 / 2,495,704 bytes differ (98.4694%).

Interpretation:

- These are not tiny incremental snapshots; broad-state serialization is changing across files.

### 4) Fixed-record stride hypotheses (firm-array candidate work)

Status: **initial scan extracted**

What is confirmed:

- Stride scan (32..768, step 4) repeatedly ranks the upper band (`~752-768`) as lowest adjacent-record similarity, across all saves.
- Top candidate currently is `768` bytes in all three saves.

Interpretation:

- This does **not** prove firm struct size yet.
- It does provide a strong first target band for deeper slicing + semantic field checks.

### 5) Bounded start/stride window coherence scan

Status: **initial extraction complete**

What is confirmed:

- Added bounded scanning across starts + stride band (`752..768`) with cross-save record delta scoring.
- Current top windows are all at start `0x000000` with the lowest score at stride `752`.
- Top five (by lowest average cross-save record delta):
	- `(start=0, stride=752)` -> `0.407379`
	- `(start=0, stride=756)` -> `0.410501`
	- `(start=0, stride=760)` -> `0.413583`
	- `(start=0, stride=764)` -> `0.416626`
	- `(start=0, stride=768)` -> `0.419637`

Interpretation:

- The candidate band remains stable.
- Window scoring currently prefers regions near the file head; this likely includes metadata/header overlap, so the next pass should skip early offsets and compare deeper starts.

### 6) First u32 field volatility classification pass

Status: **prototype extracted**

What is confirmed:

- Added per-offset u32 classification over candidate records (`stride=768`, `start=0`, first 512 records).
- Across all three saves, every 4-byte offset in this region currently classifies as `volatile`.

Interpretation:

- The current classifier is useful for plumbing/output validation, but the chosen region (`start=0`) is too mixed/noisy.
- Next refinement should classify at alternate starts from the window scan and incorporate cross-save/per-record stability signals.

## Implemented scripts

- `dev/extract_basics.py`
	- Produces `dev/out/baseline_report.json`.
- `dev/scan_stride_candidates.py`
	- Produces `dev/out/stride_candidates.json`.
- `dev/scan_windows.py`
	- Produces `dev/out/window_scan.json`.
	- Bounded defaults are tuned to finish quickly in this environment.
- `dev/classify_fields.py`
	- Produces `dev/out/field_classification.json`.

## Next steps

1. Re-run `scan_windows.py` with a non-zero start floor to avoid header bias and target mid-file regions.
2. Extend `classify_fields.py` to classify both u32 and f32 interpretations and emit confidence hints.
3. Add low-cardinality/id heuristics (including per-offset entropy) across candidate windows.
4. Add monotonic accumulator detection over per-record temporal ordering once sequential saves are confirmed.
5. Start carving sub-entity/unit regions by detecting repeated mini-blocks within candidate firm records.

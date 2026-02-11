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
- Current top windows are now from non-zero starts (default `--start-min 65536`) with the lowest score still in the same stride band.
- Top five (by lowest average cross-save record delta):
	- `(start=1761280, stride=756)` -> `0.995439`
	- `(start=1761280, stride=768)` -> `0.995449`
	- `(start=1761280, stride=764)` -> `0.995453`
	- `(start=1761280, stride=760)` -> `0.995463`
	- `(start=1761280, stride=752)` -> `0.995464`

Interpretation:

- The candidate band remains stable.
- The candidate stride band remains stable even after skipping header-heavy bytes.
- Absolute deltas are much higher in these deeper regions, which suggests we need per-scenario normalization and potentially temporal (same-company, different-month) save pairs for stronger semantic inference.

### 6) First u32/f32 field classification pass

Status: **prototype extracted**

What is confirmed:

- Added per-offset dual interpretation classification (`u32` + `f32`) over candidate records.
- The report now includes class confidence values and u32 Shannon entropy per offset.
- Current default run (`stride=768`, `start=65536`, first 512 records) provides a cleaner baseline than the original header-aligned pass.

Interpretation:

- Dual interpretation helps identify offsets that are implausible as float fields.
- Next refinement should add stronger id/enum heuristics and temporal monotonic checks over sequential saves.


### 7) Human-readable per-save output (single input -> single json)

Status: **implemented**

What is confirmed:

- Added `alogicla/xyz.py` as a stable CLI entrypoint:
	- `python alogicla/xyz.py -i <input.SAV> -o <output.json>`
- The script emits a human-readable JSON profile for one save file, including:
	- header u32 words + first bytes hex
	- byte distribution + overall entropy
	- top ascii runs
	- chunk-level entropy hotspots/coldspots
- Pre-generated outputs now exist for all current saves:
	- `alogicla/out/SPIK_001.json`
	- `alogicla/out/SPIK_002.json`
	- `alogicla/out/SPIK_003.json`

Interpretation:

- We now have a predictable per-file artifact format that can be consumed by later struct-inference scripts and manual review.
- This also gives a concrete "first-pass decode" output for each save without requiring multi-file comparisons.

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
- `alogicla/xyz.py`
	- Produces one human-readable JSON per input save (`-i` / `-o`).

## Next steps

1. Add a report comparer that diffs `alogicla/out/*.json` between runs to surface meaningful changes quickly.
2. Add low-cardinality/id heuristics that detect stable-per-record but variable-across-record fields.
3. Add monotonic accumulator detection over per-record temporal ordering once sequential saves are confirmed.
4. Add repeated-subblock detection inside candidate records to carve unit-layer mini-structs.
5. Add a firm-record candidate exporter that writes decoded table rows per hypothesized stride/start.

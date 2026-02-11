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

## Implemented scripts

- `dev/extract_basics.py`
	- Produces `dev/out/baseline_report.json`.
- `dev/scan_stride_candidates.py`
	- Produces `dev/out/stride_candidates.json`.

## Next steps

1. Add a bounded scanner that tests candidate starts + stride `752..768` and measures month-to-month delta coherence.
2. Build a u32/f32 field volatility classifier per offset within each candidate stride.
3. Detect likely id/categorical fields (low cardinality, mostly constant per record).
4. Isolate monotonic accumulators (candidate lifetime revenue/profit counters).
5. Start carving sub-entity/unit regions by detecting repeated mini-blocks within candidate firm records.

# logical

Human-readable save summaries.

## Main command

```bash
python logical/extract_save_summary.py -i SPIK_001.SAV -o logical/out/SPIK_001.json
```

The CLI always follows:

```bash
python logical/extract_save_summary.py -i <input.SAV> -o <output.json>
```

## Comparison command

```bash
python logical/compare_summaries.py -i logical/out/SPIK_001.json logical/out/SPIK_002.json logical/out/SPIK_003.json -o logical/out/comparison_overview.json
```

## Output style

The summary JSON is intentionally logical and human-readable:

- scenario and source path
- world snapshot health (size, density, entropy)
- company and firm-level placeholders for progressive decoding
- no raw offset-level sections

## Included outputs

- `logical/out/SPIK_001.json`
- `logical/out/SPIK_002.json`
- `logical/out/SPIK_003.json`
- `logical/out/comparison_overview.json`

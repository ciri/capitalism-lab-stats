# Save Decoding Roadmap

## Current baseline

- Replaced typo path (`alogicla`) with a logical location: `logical/`.
- Replaced `xyz.py` with `logical/extract_save_summary.py`.
- Main command is now:
	- `python logical/extract_save_summary.py -i <input.SAV> -o <output.json>`
- Generated human-readable outputs for each save in `logical/out/`.
- Added comparison command:
	- `python logical/compare_summaries.py -i <summary1.json> <summary2.json> ... -o <comparison.json>`

## Output contract (human-readable only)

Each summary JSON focuses on business-readable fields, including:

- scenario and source path
- world snapshot health
- company/firms summary
- store/factory placeholders when not inferable yet

No raw offset-oriented reporting in this layer.

## Next steps

1. Extract probable firm/store counts from repeated-record heuristics and fill currently unknown fields.
2. Add inferred corporation-level metrics (cash/debt-like candidates) with confidence labels.
3. Add export modes: executive summary markdown + JSON.
4. Add a dedicated data-quality section to highlight confidence per logical field.

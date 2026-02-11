# alogicla

Human-readable extraction entrypoint for individual save files.

## Main script

```bash
python alogicla/xyz.py -i data/saves/SPIK_001.SAV -o alogicla/out/SPIK_001.json
```

## Output contents

Each output JSON includes:

- basic file metadata (`name`, `size_bytes`)
- header words (`u32_words`, first bytes as hex)
- byte distribution (`zero_ratio`, overall entropy)
- top ascii runs (useful for anchor strings)
- chunked region entropy map (highest + lowest entropy chunks)

Pre-generated examples are available in `alogicla/out/` for all current `.SAV` files.

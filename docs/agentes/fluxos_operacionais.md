# Fluxos Operacionais

## Metadata

```powershell
uv run python -m src.gbif.metadata.bronze.extract_datasets --date 20260504 --limit 100
uv run python -m src.gbif.metadata.silver.build_silver_dataset --date 20260504
uv run python -m src.gbif.gold.build_metadata --date 20260504
```

## Occurrence

```powershell
uv run python -m src.gbif.occurrence.bronze.extract_occurrences --date 20260504 --country BR --limit 100
uv run python -m src.gbif.occurrence.silver.build_silver_dataset --date 20260504
uv run python -m src.gbif.gold.build_occurrence --date 20260504
```

## Gold

Mapa de produtos:

```text
silver/occurrence -> gold/occurrence
silver/metadata   -> gold/metadata
silver/checklist  -> gold/checklist
silver/sampling_event -> gold/sampling_event
```

```powershell
uv run python -m src.gbif.gold.build_metadata --date 20260504
uv run python -m src.gbif.gold.build_occurrence --date 20260504
```

Cada produto gold gera:

```text
arquivo de dados final
schema.json
quality_report.json
manifest.json
```

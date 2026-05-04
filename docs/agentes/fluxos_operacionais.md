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

## Especies Ameacadas no Brasil

Fluxo inicial sem conta GBIF:

```powershell
uv run python -m src.gbif.reference.threatened_species_brazil.download_official_reference
uv run python -m src.gbif.reference.threatened_species_brazil.build_reference
uv run python -m src.gbif.reference.threatened_species_brazil.reconcile_gbif_taxonomy
uv run python -m src.gbif.reference.threatened_species_brazil.apply_gbif_taxonomy_matches
uv run python -m src.gbif.occurrence.bronze.extract_threatened_occurrences --date 20260504 --species-limit 10 --occurrence-limit-per-species 100
uv run python -m src.gbif.gold.build_threatened_species_brazil --snapshot-date 2026-05-04
uv run python -m src.gbif.gold.build_threatened_species_occurrences --date 20260504
uv run python -m src.gbif.gold.build_threatened_species_datasets
uv run python -m src.gbif.gold.build_threatened_species_geopackage
```

Observacoes:

- `download_official_reference` baixa recursos CSV/PDF do conjunto oficial do MMA em Dados Abertos.
- `build_reference` normaliza a referencia MMA para `threatened_species_brazil_reference.json`.
- Por padrao, `build_reference` mantem todas as categorias observadas na referencia oficial.
- `reconcile_gbif_taxonomy` usa a API publica `species/match` do GBIF para obter `taxonKey` e nome aceito.
- `apply_gbif_taxonomy_matches` gera `threatened_species_brazil_reference_gbif_matched.json` com os campos taxonomicos preenchidos.
- `extract_threatened_occurrences` usa `/occurrence/search` com `country=BR` e `taxonKey`.
- `build_threatened_species_occurrences` gera `occurrences.json` a partir do bronze de ocorrencias.
- `build_threatened_species_datasets` gera `datasets.json` a partir dos `dataset_key` observados nas ocorrencias e metadados publicos do GBIF.
- `build_threatened_species_geopackage` gera `threatened_species_occurrences.gpkg` com ocorrencias georreferenciadas em `EPSG:4326`.
- Para carga grande de ocorrencias, trocar o ultimo passo pela Download API assincrona quando houver conta GBIF.
- A referencia MMA 2021 em CSV e operacional/provisoria para desenvolvimento do pipeline; antes da gold final, validar contra as portarias MMA vigentes.
- Para a primeira versao operacional, foi decidido usar MMA Dados Abertos 2021 como referencia da gold.

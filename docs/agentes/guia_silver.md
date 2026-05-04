# Guia Silver

## Objetivo

A camada `silver` converte snapshots brutos do GBIF em bases canonicas por classe.

## Saidas

```text
data/gbif/02_silver/occurrence/YYYYMMDD/allrecords.json
data/gbif/02_silver/checklist/YYYYMMDD/alltaxa.json
data/gbif/02_silver/sampling_event/YYYYMMDD/allevents.json
data/gbif/02_silver/sampling_event/YYYYMMDD/alloccurrences.json
data/gbif/02_silver/metadata/YYYYMMDD/alldatasets.json
```

## Regras

- Preservar `snapshot_date`.
- Preservar `bronze_file_path`.
- Converter vazios para `null`.
- Nao imputar informacao ausente.
- Gerar `quality_report.json`.


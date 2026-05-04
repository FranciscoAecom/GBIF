# Metadata Integration Notes

## Endpoint

- `GET https://api.gbif.org/v1/dataset/search`

## Uso Inicial

O extrator salva:

- `query/request.json`
- `pages/page_*.json`
- `records/<dataset_key>.json`

## Parametros

- `type`: `OCCURRENCE`, `CHECKLIST`, `SAMPLING_EVENT` ou `METADATA`
- `q`: busca textual
- `limit`: limite local de registros coletados


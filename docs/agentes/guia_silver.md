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
- Preservar datas originais em `event_date`.
- Criar campos ACM de data normalizada quando houver dia completo.
- Preservar coordenadas originais do GBIF.
- Criar campos ACM de coordenada para uso espacial e classificacao de qualidade.
- Gerar `quality_report.json`.
- Para bases potencialmente grandes, como `occurrence`, ler e escrever registros de forma incremental sempre que possivel.
- `occurrence` e `metadata` ja seguem o padrao de escrita incremental em JSON para evitar acumulo desnecessario em memoria.

## Datas em occurrence

O campo `event_date` deve preservar o valor original recebido do GBIF.

A silver tambem cria:

```text
acm_event_date
acm_event_date_precision
acm_event_date_issue
```

Regras:

- `2018-04-30` vira `acm_event_date = 2018-04-30` e precisao `DAY`.
- `1981-12-23T00:00:00` vira `acm_event_date = 1981-12-23` e precisao `DATETIME`.
- `1974-07` nao vira `1974-07-01`; fica sem `acm_event_date` e precisao `MONTH`.
- `1992` nao vira `1992-01-01`; fica sem `acm_event_date` e precisao `YEAR`.
- intervalos, datas impossiveis ou formatos nao reconhecidos ficam sem `acm_event_date` e recebem uma classificacao em `acm_event_date_precision` e `acm_event_date_issue`.

Essa regra evita criar datas artificiais.

## Coordenadas em occurrence

Os campos originais do GBIF devem ser preservados:

```text
decimal_latitude
decimal_longitude
```

A silver tambem cria:

```text
acm_decimal_latitude
acm_decimal_longitude
acm_coordinate_was_swapped
acm_coordinate_status
acm_coordinate_issue
```

Regras:

- se a coordenada original cai na caixa aproximada do Brasil, o status e `VALID_ORIGINAL`.
- se a coordenada original cai fora do Brasil, mas latitude/longitude invertidas caem no Brasil, o status e `POSSIBLE_SWAPPED` e `acm_coordinate_was_swapped = true`.
- se a coordenada original tem alerta do GBIF, mas a inversao latitude/longitude cai no Brasil, o status fica `POSSIBLE_SWAPPED`.
- se o GBIF marcou problema geoespacial e a inversao nao resolve, o status e `GBIF_GEOSPATIAL_ISSUE`.
- se a coordenada cai fora da caixa aproximada do Brasil mesmo apos testar inversao, o status e `OUTSIDE_BRAZIL_BBOX`.
- se a coordenada esta ausente ou invalida, o status e `MISSING_OR_INVALID`.

O GeoPackage deve usar `acm_decimal_latitude` e `acm_decimal_longitude`.
As coordenadas originais continuam disponiveis para auditoria.

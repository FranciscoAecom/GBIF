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
- Criar campos ACM de estado e municipio por intersecao com malhas IBGE quando houver coordenada valida.
- Gerar `quality_report.json`.
- Para bases potencialmente grandes, como `occurrence`, ler e escrever registros de forma incremental sempre que possivel.
- `occurrence` e `metadata` ja seguem o padrao de escrita incremental em JSON para evitar acumulo desnecessario em memoria.

## Datas em occurrence

O campo `event_date` deve preservar o valor original recebido do GBIF.

A silver tambem cria:

```text
acm_event_date
```

Regras:

- `2018-04-30` vira `acm_event_date = 2018-04-30`.
- `1981-12-23T00:00:00` vira `acm_event_date = 1981-12-23`.
- `1974-07` nao vira `1974-07-01`; fica sem `acm_event_date`.
- `1992` nao vira `1992-01-01`; fica sem `acm_event_date`.
- intervalos, datas impossiveis ou formatos nao reconhecidos ficam sem `acm_event_date`.

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
```

Regras:

- se a coordenada original cai na caixa aproximada do Brasil, ela e copiada para os campos ACM.
- se a coordenada original cai fora do Brasil, mas latitude/longitude invertidas caem no Brasil, os campos ACM recebem a coordenada invertida.
- se o GBIF marcou problema geoespacial e a inversao nao resolve, os campos ACM ficam vazios.
- se a coordenada cai fora da caixa aproximada do Brasil mesmo apos testar inversao, os campos ACM ficam vazios.
- se a coordenada esta ausente ou invalida, os campos ACM ficam vazios.

O GeoPackage deve usar `acm_decimal_latitude` e `acm_decimal_longitude`.
As coordenadas originais continuam disponiveis para auditoria.

## Localidade em occurrence

Os campos originais devem ser preservados:

```text
state_province
municipality
```

A gold de especies ameacadas cria:

```text
acm_state_province
acm_municipality
```

Regras:

- os campos originais `state_province` e `municipality` continuam como vieram do GBIF.
- `acm_state_province` e obtido pela intersecao da coordenada ACM com a malha de estados do IBGE.
- `acm_municipality` e obtido pela intersecao da coordenada ACM com a malha de municipios do IBGE.
- Quando a ocorrencia nao tem coordenada ACM valida, os campos de localidade ACM ficam `null`.

## Duplicidade espacial

A silver/gold deve preservar todos os registros no JSON.
Duplicidades espaciais nao devem ser apagadas de `occurrences.json`.

Para consumo cartografico, o GeoPackage pode remover duplicidades usando a chave:

```text
species_id + acm_decimal_latitude + acm_decimal_longitude
```

No fluxo geral sem `species_id`, a chave tecnica equivalente pode usar `taxon_key`.

Essa regra significa:

- JSON final = base completa e auditavel
- GeoPackage = camada de mapa deduplicada

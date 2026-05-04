# Piloto - Especies Ameacadas no Brasil

## Objetivo

Validar o fluxo ponta a ponta para montar a base `gold` de especies ameacadas no Brasil usando:

- referencia MMA 2021
- reconciliacao taxonomica com GBIF
- busca publica de ocorrencias GBIF no Brasil
- geracao dos arquivos finais da gold
- geracao de GeoPackage para visualizacao espacial

Este piloto nao representa a carga completa. Ele foi feito com volume pequeno para validar metodo, estrutura, campos e rastreabilidade.

## Fonte de Referencia

Fonte usada:

```text
MMA Dados Abertos - Especies Ameacadas
FAUNA - Lista de Especies Ameacadas - 2021.csv
FLORA - Lista de Especies Ameacadas - 2021.csv
```

Decisao do projeto:

- usar MMA Dados Abertos 2021 como referencia da primeira versao operacional
- manter portarias posteriores como melhoria ou validacao futura
- preservar essa decisao no `manifest.json`

Quantidade na referencia normalizada:

```text
4.619 registros/especies
4.617 com taxon_key GBIF apos reconciliacao
```

## Escopo do Piloto

O piloto usou apenas as primeiras 10 especies da referencia reconciliada:

```text
Condylactis gigantea
Charinus acaraje
Charinus asturius
Charinus caatingae
Charinus eleonorae
Charinus ferreus
Charinus potiguar
Charinus spelaeus
Charinus taboa
Charinus troglobius
```

Filtro usado na API GBIF:

```text
country = BR
taxonKey = <taxon_key da especie>
```

Limites do piloto:

```text
species-limit = 10
occurrence-limit-per-species = 100
```

Comando usado:

```powershell
uv run python -m src.gbif.occurrence.bronze.extract_threatened_occurrences --date 20260504 --species-limit 10 --occurrence-limit-per-species 100 --page-size 100 --sleep-seconds 0.1
```

## Fluxo Validado

1. Baixar referencia oficial operacional do MMA.
2. Normalizar a lista MMA.
3. Reconciliar nomes com a API `species/match` do GBIF.
4. Gerar `species.json`.
5. Buscar ocorrencias GBIF no Brasil para as especies do piloto.
6. Gerar `occurrences.json`.
7. Identificar datasets de origem e gerar `datasets.json`.
8. Gerar GeoPackage com ocorrencias que possuem coordenadas validas.
9. Atualizar `manifest.json`, `schema.json` e relatorios de qualidade.

## Resultados

Resumo do piloto:

```text
10 especies testadas
124 ocorrencias GBIF encontradas no Brasil
10 datasets de origem
74 ocorrencias com coordenadas validas
50 ocorrencias sem coordenadas validas
```

Distribuicao das ocorrencias por categoria MMA no piloto:

```text
EN: 55
CR: 38
VU: 31
```

GeoPackage gerado:

```text
data/gbif/03_gold/threatened_species_brazil/threatened_species_occurrences.gpkg
```

Caracteristicas do GeoPackage:

```text
74 feicoes
Geometria: Point
CRS: EPSG:4326
Camada: threatened_species_occurrences
```

## Arquivos Gold Gerados no Piloto

```text
data/gbif/03_gold/threatened_species_brazil/species.json
data/gbif/03_gold/threatened_species_brazil/occurrences.json
data/gbif/03_gold/threatened_species_brazil/datasets.json
data/gbif/03_gold/threatened_species_brazil/threatened_species_occurrences.gpkg
data/gbif/03_gold/threatened_species_brazil/manifest.json
data/gbif/03_gold/threatened_species_brazil/schema.json
data/gbif/03_gold/threatened_species_brazil/quality_report.json
data/gbif/03_gold/threatened_species_brazil/occurrences_quality_report.json
data/gbif/03_gold/threatened_species_brazil/datasets_quality_report.json
```

## Rastreabilidade

O piloto preserva rastreabilidade por meio de:

- `species.source_reference_path`
- `occurrences.bronze_file_path`
- `occurrences.dataset_key`
- `datasets.dataset_key`
- `manifest.json`

O `manifest.json` registra:

- fonte de referencia usada
- decisao de usar MMA Dados Abertos 2021 na primeira versao operacional
- snapshot de ocorrencias
- bundle bronze de origem
- quantidade de registros
- quantidade de feicoes no GeoPackage

## Limitacoes

Este piloto tem limitacoes importantes:

- considera apenas 10 especies
- usa `/occurrence/search`, nao a Download API assincrona
- nao representa a carga completa das 4.619 especies da referencia
- nao usa ainda conta GBIF
- o GeoPackage inclui apenas ocorrencias com latitude e longitude validas
- ocorrencias sem coordenadas ficam preservadas em `occurrences.json`, mas nao aparecem no mapa
- `sampling_event` ainda nao foi usado para enriquecer metodo/protocolo/esforco
- a referencia MMA 2021 foi adotada como primeira versao operacional; portarias posteriores ficam para validacao futura

## Proximos Passos

1. Criar conta GBIF para usar Download API assincrona.
2. Implementar download assincrono para carga completa.
3. Rodar a carga completa para todas as especies da referencia.
4. Avaliar tratamento futuro de ocorrencias sem coordenadas.
5. Enriquecer com `sampling_event` quando houver relacionamento disponivel.
6. Validar referencia MMA 2021 contra portarias posteriores.


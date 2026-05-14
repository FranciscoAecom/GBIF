# GBIF Pipelines

Pipelines para coletar, preservar, padronizar e consolidar dados publicos do
GBIF em camadas `bronze`, `silver` e `gold`.

O projeto organiza dados das quatro classes principais de datasets GBIF:

- `occurrence`: registros de ocorrencia de organismos.
- `checklist`: listas de nomes, taxons e usos taxonomicos.
- `sampling_event`: eventos de amostragem e ocorrencias associadas.
- `metadata`: metadados de datasets e recursos.

## Objetivo

O repositorio foi criado para:

- extrair dados brutos da API do GBIF;
- preservar snapshots brutos na camada `bronze`;
- transformar dados para estruturas canonicas na camada `silver`;
- consolidar produtos analiticos na camada `gold`;
- manter rastreabilidade entre produto final, snapshot GBIF e referencias usadas.

O produto analitico prioritario atual e a base `gold` de especies ameacadas no
Brasil, combinando referencia oficial brasileira, taxonomia GBIF, ocorrencias,
metadados de datasets e saida espacial em GeoPackage.

## Estrutura

```text
src/gbif/
|-- checklist/
|-- metadata/
|-- occurrence/
|-- reference/
|-- sampling_event/
|-- shared/
`-- gold/

data/gbif/
|-- 00_reference/
|-- 01_bronze/
|-- 02_silver/
`-- 03_gold/

docs/agentes/
tests/
```

Camadas principais:

- `data/gbif/00_reference/`: fontes externas de referencia, como MMA e IBGE.
- `data/gbif/01_bronze/`: snapshots brutos preservados.
- `data/gbif/02_silver/`: dados normalizados e canonicos.
- `data/gbif/03_gold/`: produtos analiticos finais.

## Requisitos

- Python 3.11 ou superior.
- `uv` para ambiente, dependencias e execucao.

Instalacao das dependencias:

```powershell
uv sync
```

Todos os comandos operacionais devem ser executados com:

```powershell
uv run python -m ...
```

## Fluxo Principal: Especies Ameacadas no Brasil

Gerar as referencias oficiais e reconciliar a taxonomia com o GBIF:

```powershell
uv run python -m src.gbif.reference.threatened_species_brazil.download_official_reference
uv run python -m src.gbif.reference.threatened_species_brazil.build_reference
uv run python -m src.gbif.reference.threatened_species_brazil.reconcile_gbif_taxonomy
uv run python -m src.gbif.reference.threatened_species_brazil.apply_gbif_taxonomy_matches
uv run python -m src.gbif.reference.ibge.download_reference
```

Preparar, enviar, acompanhar e baixar um pedido assincrono de ocorrencias no
GBIF:

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download prepare --date YYYYMMDD
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download submit --date YYYYMMDD
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download status --date YYYYMMDD --download-key <download_key>
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download download --date YYYYMMDD --download-key <download_key>
```

Quando o ZIP oficial do GBIF ja estiver baixado, executar o pipeline completo da
gold:

```powershell
uv run python -m src.gbif.gold.run_threatened_species_pipeline --date YYYYMMDD --snapshot-date YYYY-MM-DD --download-key <download_key>
```

Validar os produtos gerados:

```powershell
uv run python -m src.gbif.gold.validate_threatened_species_brazil
```

Saida esperada:

```text
data/gbif/03_gold/threatened_species_brazil/
|-- species.json
|-- occurrences.json
|-- datasets.json
|-- threatened_species_occurrences.gpkg
|-- schema.json
|-- quality_report.json
`-- manifest.json
```

## Credenciais GBIF

O download assincrono do GBIF exige conta GBIF. As credenciais devem ficar
apenas em variaveis de ambiente:

```powershell
$env:GBIF_USERNAME="usuario_gbif"
$env:GBIF_PASSWORD="senha_gbif"
$env:GBIF_EMAIL="email_da_conta"
```

A senha nao deve ser salva em codigo, documentacao, manifest ou arquivo de
configuracao.

## Regras de Dados

### Bronze

- Guarda respostas brutas da API sem transformacao analitica.
- Todo snapshot deve usar `--date` no formato `YYYYMMDD`.
- Ao final, snapshots compactados devem seguir o padrao `YYYYMMDD_core.zip`.
- Pastas descompactadas como `pages/`, `records/`, `query/`, `raw/` e
  `downloads/` nao devem ser versionadas.
- Bundles compactados podem ser versionados via Git LFS.

### Silver

- Transforma o bronze em dados tabulares canonicos.
- Cada registro deve preservar `snapshot_date` e `bronze_file_path`.
- Campos ausentes devem ficar como `null`.
- Normalizacoes devem ser deterministicas e documentadas.

### Gold

- Produtos finais nascem da `silver` e das referencias oficiais.
- Produtos especiais podem ler ZIP oficial do `bronze` diretamente quando isso
  preservar o pacote GBIF original ou permitir processamento em streaming.
- Produtos finais devem ter `schema.json`, `quality_report.json` e
  `manifest.json`.
- Bases grandes reproduziveis podem ser sobrescritas a partir do bronze,
  referencia e manifest.

## Testes

Executar a suite:

```powershell
uv run pytest
```

## Documentacao

Documentos detalhados ficam em `docs/agentes/`, especialmente:

- `docs/agentes/fluxos_operacionais.md`
- `docs/agentes/especies_ameacadas_brasil.md`
- `docs/agentes/guia_bronze.md`
- `docs/agentes/guia_silver.md`
- `docs/agentes/guia_gold.md`


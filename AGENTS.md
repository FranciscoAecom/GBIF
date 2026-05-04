# AGENTS

Este repositorio coleta, preserva e padroniza dados publicos do GBIF.

## Objetivo

- Extrair dados brutos da API do GBIF.
- Preservar snapshots brutos na camada `bronze`.
- Transformar os dados para estruturas canonicas na camada `silver`.
- Consolidar produtos analiticos na camada `gold`.

## Ambiente Python

- O projeto deve ser executado com `uv`.
- Dependencias principais ficam em `pyproject.toml`.
- O arquivo `uv.lock` deve ser versionado para manter instalacoes reproduziveis.
- Comandos operacionais devem usar `uv run python -m ...`.

## Classes GBIF

O projeto segue as quatro classes principais de datasets do GBIF:

- `occurrence`: registros de ocorrencia de organismos.
- `checklist`: listas de nomes, taxons e usos taxonomicos.
- `sampling_event`: eventos de amostragem e ocorrencias associadas.
- `metadata`: metadados de datasets e recursos.

## Estrutura Padrao

```text
src/gbif/<classe>/bronze/
src/gbif/<classe>/silver/
data/gbif/01_bronze/<classe>/
data/gbif/02_silver/<classe>/
data/gbif/03_gold/
```

## Regras Bronze

- A camada `bronze` guarda respostas brutas da API sem transformacao analitica.
- Todo snapshot deve ser orientado por `--date` no formato `YYYYMMDD`.
- Durante a execucao, o snapshot pode existir descompactado.
- Ao final, o snapshot deve ser compactado como `YYYYMMDD_core.zip`.
- Dados descompactados como `pages/`, `records/`, `query/`, `raw/` e `downloads/` nao devem ser versionados.
- Bundles compactados de bronze podem ser versionados via Git LFS.

## Regras Silver

- A camada `silver` transforma o bronze em dados tabulares canonicos.
- Cada registro deve preservar `snapshot_date` e `bronze_file_path`.
- Campos ausentes devem ficar como `null`.
- Normalizacoes devem ser deterministicas e documentadas.

## Regras Gold

- A camada `gold` nasce da `silver`, nao volta ao `bronze`.
- Produtos finais devem ter `schema.json` e `quality_report.json`.
- Bases antigas devem ser preservadas em `backup/` antes de sobrescrita.

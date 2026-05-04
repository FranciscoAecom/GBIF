# Guia Gold

## Objetivo

A camada `gold` consolida produtos analiticos finais derivados da camada `silver`.

## Produtos Iniciais

```text
data/gbif/03_gold/occurrence/
data/gbif/03_gold/metadata/
data/gbif/03_gold/checklist/
data/gbif/03_gold/sampling_event/
```

## Estrutura Espelhada

A camada `gold` deve manter a mesma estrutura de classes usada em `bronze` e `silver`.

Mapa vigente:

```text
bronze/occurrence -> silver/occurrence -> gold/occurrence
bronze/metadata   -> silver/metadata   -> gold/metadata
bronze/checklist  -> silver/checklist  -> gold/checklist
bronze/sampling_event -> silver/sampling_event -> gold/sampling_event
```

Leitura conceitual:

- `occurrence` continua em `occurrence`, mas o arquivo final pode se chamar `allrecords.json`.
- `metadata` continua em `metadata`, mas o arquivo final pode se chamar `alldatasets.json`.
- `checklist` continua em `checklist`, e a saida prevista e `alltaxa.json`.
- `sampling_event` continua em `sampling_event`, com saidas previstas para eventos e ocorrencias associadas.

Essa simetria facilita localizar a origem de cada base: a classe GBIF e a mesma nas tres camadas.

## Regras

- A `gold` deve nascer da `silver`.
- Nao deve consultar o `bronze` diretamente.
- Deve produzir o arquivo de dados final, `schema.json`, `quality_report.json` e `manifest.json`.
- Deve fazer backup antes de sobrescrever bases existentes.

## Manifesto

Cada produto `gold` deve ter um `manifest.json`.

Esse arquivo funciona como documento de identidade da base final e deve registrar:

- produto gold gerado
- classe GBIF de origem
- snapshot `silver` usado
- arquivo `silver` de origem
- bundle `bronze` de origem
- data/hora de geracao
- quantidade de registros

Exemplo conceitual:

```json
{
  "product": "occurrence",
  "source_class": "occurrence",
  "source_silver_snapshot": "20260504",
  "source_silver_file": "data/gbif/02_silver/occurrence/20260504/allrecords.json",
  "source_bronze_bundle": "data/gbif/01_bronze/occurrence/20260504_core.zip",
  "generated_at": "2026-05-04T11:30:00",
  "record_count": 2
}
```

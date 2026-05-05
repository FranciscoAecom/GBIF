# Guia Gold

## Objetivo

A camada `gold` consolida produtos analiticos finais derivados da camada `silver`.

## Produtos por Classe GBIF

```text
data/gbif/03_gold/occurrence/
data/gbif/03_gold/metadata/
data/gbif/03_gold/checklist/
data/gbif/03_gold/sampling_event/
```

## Produto Analitico Prioritario

O foco analitico do projeto e montar uma base de especies ameacadas no Brasil:

```text
data/gbif/03_gold/threatened_species_brazil/
```

Esse produto nao precisa espelhar uma unica classe GBIF. Ele deve combinar dados das camadas `silver` relevantes, principalmente:

- `silver/checklist`, para taxonomia e nomes
- `silver/occurrence`, para ocorrencias no Brasil
- `silver/metadata`, para datasets de origem
- `silver/sampling_event`, opcionalmente, para enriquecer ocorrencias com metodo, protocolo e esforco de amostragem quando disponivel

Tambem deve cruzar essas bases com uma referencia oficial de especies ameacadas no Brasil.

Fonte principal definida:

- MMA / Lista Nacional Oficial de Especies Ameacadas

Fontes tecnicas de apoio:

- ICMBio para fauna
- CNCFlora/JBRJ para flora

Fonte complementar:

- IUCN, somente quando for util comparar status global e status nacional

## Estrutura Espelhada

A camada `gold` pode ter dois tipos de produtos:

- produtos por classe GBIF, mantendo a mesma estrutura de `bronze` e `silver`
- produtos analiticos finais, como `threatened_species_brazil`

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

No caso de `threatened_species_brazil`, a rastreabilidade deve ser garantida pelo `manifest.json`, porque o produto final combina multiplas fontes.

O schema canonico inicial desse produto esta documentado em:

```text
docs/agentes/especies_ameacadas_brasil.md
```

O metodo de construcao desse produto tambem esta documentado nesse arquivo, incluindo o papel de `checklist`, `occurrence`, `metadata` e `sampling_event`.

## Regras

- A `gold` deve nascer da `silver`.
- Nao deve consultar o `bronze` diretamente.
- Deve produzir o arquivo de dados final, `schema.json`, `quality_report.json` e `manifest.json`.
- Deve fazer backup antes de sobrescrever bases existentes.
- Quando o produto tiver componente espacial, como `threatened_species_brazil`, deve produzir tambem `.gpkg` com CRS `EPSG:4326`.

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
  "source_silver_snapshot": "YYYYMMDD",
  "source_silver_file": "data/gbif/02_silver/occurrence/YYYYMMDD/allrecords.json",
  "source_bronze_bundle": "data/gbif/01_bronze/occurrence/YYYYMMDD_core.zip",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "record_count": 0
}
```

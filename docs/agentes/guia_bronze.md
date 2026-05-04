# Guia Bronze

## Objetivo

A camada `bronze` preserva a resposta bruta da API do GBIF.

## Estrutura

```text
data/gbif/01_bronze/<classe>/YYYYMMDD_core.zip
```

Durante execucao:

```text
data/gbif/01_bronze/<classe>/YYYYMMDD/
|-- query/request.json
|-- pages/page_000001.json
`-- records/<id>.json
```

## Regras

- Nao normalizar valores no bronze.
- Salvar a consulta usada em `query/request.json`.
- Salvar paginas da API em `pages/`.
- Quando houver identificador estavel, salvar tambem um arquivo por registro em `records/`.
- Compactar o snapshot ao fim da execucao.


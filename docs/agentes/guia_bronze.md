# Guia Bronze

## Objetivo

A camada `bronze` preserva o dado bruto recebido do GBIF.

Esse dado pode vir de duas formas:

- respostas de endpoints publicos da API, para consultas pequenas ou diagnosticos
- ZIP oficial da Download API assincrona, para volumes grandes de ocorrencias

## Estrutura

Para snapshots compactados gerados pelo pipeline:

```text
data/gbif/01_bronze/<classe>/YYYYMMDD_core.zip
```

Para downloads assincronos oficiais do GBIF:

```text
data/gbif/01_bronze/<classe>/YYYYMMDD/downloads/<download_key>.zip
```

Durante execucao de coletas paginadas:

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
- Em download assincrono, preservar o ZIP oficial baixado do GBIF e o manifest com `download_key`, filtros e data do pedido.

Para `occurrence` via API paginada, o extrator deve ser usado apenas em consultas pequenas ou diagnosticos.
Ele grava registros incrementalmente em `records/`, mas tambem preserva a resposta completa de cada pagina em `pages/`.

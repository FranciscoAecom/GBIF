# Premissas do Projeto GBIF

## Escopo

O projeto trabalha com dados publicos disponibilizados pelo GBIF por meio das APIs oficiais.

Para consultas pequenas, diagnosticos e metadados, pode usar endpoints publicos.
Para volumes grandes de ocorrencias, deve usar a Download API assincrona do GBIF com conta.

## Camadas

- `bronze`: dado bruto recebido do GBIF, seja resposta de API ou ZIP oficial de download assincrono, versionado por snapshot.
- `silver`: estrutura canonica por classe GBIF.
- `gold`: produtos analiticos consolidados, incluindo a futura base de especies ameacadas no Brasil.

## Classes

- `occurrence`
- `checklist`
- `sampling_event`
- `metadata`

## Produto Analitico Prioritario

O produto analitico prioritario definido para a camada `gold` e uma base de especies ameacadas no Brasil:

```text
data/gbif/03_gold/threatened_species_brazil/
```

Essa base deve cruzar dados GBIF com uma referencia brasileira de especies ameacadas.

Fonte principal:

- MMA / Lista Nacional Oficial de Especies Ameacadas

Referencia operacional da primeira versao:

- MMA Dados Abertos 2021, arquivos CSV de fauna e flora

Validacao normativa futura:

- Portarias MMA vigentes e atualizacoes posteriores

Fontes tecnicas de apoio:

- ICMBio para fauna
- CNCFlora/JBRJ para flora

Fonte complementar:

- IUCN, quando houver necessidade de comparar status global com status nacional

## Politica de Arquivos Grandes

Snapshots compactados e arquivos binarios grandes devem ser versionados via Git LFS.
Arquivos intermediarios gerados e snapshots descompactados devem ficar fora do Git.

## Ambiente Python

O projeto usa `uv` para resolver dependencias, criar o ambiente virtual local e executar os scripts.

Comando base:

```powershell
uv run python -m <modulo>
```

# Premissas do Projeto GBIF

## Escopo

O projeto trabalha com dados publicos disponibilizados pelo GBIF por meio da API oficial.

## Camadas

- `bronze`: resposta bruta da API, versionada por snapshot.
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

Essa base deve cruzar dados GBIF com uma referencia oficial brasileira de especies ameacadas.

Fonte principal:

- MMA / Lista Nacional Oficial de Especies Ameacadas

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

# Premissas do Projeto GBIF

## Escopo

O projeto trabalha com dados publicos disponibilizados pelo GBIF por meio da API oficial.

## Camadas

- `bronze`: resposta bruta da API, versionada por snapshot.
- `silver`: estrutura canonica por classe GBIF.
- `gold`: produtos analiticos consolidados.

## Classes

- `occurrence`
- `checklist`
- `sampling_event`
- `metadata`

## Politica de Arquivos Grandes

Snapshots compactados e arquivos binarios grandes devem ser versionados via Git LFS.
Arquivos intermediarios gerados e snapshots descompactados devem ficar fora do Git.

## Ambiente Python

O projeto usa `uv` para resolver dependencias, criar o ambiente virtual local e executar os scripts.

Comando base:

```powershell
uv run python -m <modulo>
```

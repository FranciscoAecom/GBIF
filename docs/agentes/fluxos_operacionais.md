# Fluxos Operacionais

## Gold

Mapa de produtos:

```text
silver/occurrence -> gold/occurrence
silver/metadata   -> gold/metadata
silver/checklist  -> gold/checklist
silver/sampling_event -> gold/sampling_event
```

```powershell
uv run python -m src.gbif.gold.build_metadata --date YYYYMMDD
uv run python -m src.gbif.gold.build_occurrence --date YYYYMMDD
```

Cada produto gold gera:

```text
arquivo de dados final
schema.json
quality_report.json
manifest.json
```

## Especies Ameacadas no Brasil

Fluxo principal com conta GBIF:

```powershell
uv run python -m src.gbif.reference.threatened_species_brazil.download_official_reference
uv run python -m src.gbif.reference.threatened_species_brazil.build_reference
uv run python -m src.gbif.reference.threatened_species_brazil.reconcile_gbif_taxonomy
uv run python -m src.gbif.reference.threatened_species_brazil.apply_gbif_taxonomy_matches
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download prepare --date YYYYMMDD
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download submit --date YYYYMMDD
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download status --date YYYYMMDD --download-key <download_key>
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download download --date YYYYMMDD --download-key <download_key>
uv run python -m src.gbif.gold.build_threatened_species_brazil --snapshot-date YYYY-MM-DD
uv run python -m src.gbif.gold.build_threatened_species_occurrences --date YYYYMMDD
uv run python -m src.gbif.gold.build_threatened_species_datasets
uv run python -m src.gbif.gold.build_threatened_species_geopackage
```

Observacoes:

- `download_official_reference` baixa recursos CSV/PDF do conjunto oficial do MMA em Dados Abertos.
- `build_reference` normaliza a referencia MMA para `threatened_species_brazil_reference.json`.
- Por padrao, `build_reference` mantem todas as categorias observadas na referencia oficial.
- `reconcile_gbif_taxonomy` usa a API publica `species/match` do GBIF para obter `taxonKey` e nome aceito.
- `apply_gbif_taxonomy_matches` gera `threatened_species_brazil_reference_gbif_matched.json` com os campos taxonomicos preenchidos.
- `async_threatened_occurrence_download` usa a Download API assincrona do GBIF para volumes grandes.
- O pedido completo usa todos os `TAXON_KEY` reconciliados entre MMA e GBIF.
- Limites opcionais devem ficar restritos a testes controlados ou diagnosticos tecnicos.
- `build_threatened_species_occurrences` gera `occurrences.json` a partir do bronze de ocorrencias.
- `build_threatened_species_datasets` gera `datasets.json` a partir dos `dataset_key` observados nas ocorrencias e metadados publicos do GBIF.
- `build_threatened_species_geopackage` gera `threatened_species_occurrences.gpkg` com ocorrencias georreferenciadas em `EPSG:4326`.
- Para carga grande de ocorrencias, usar a Download API assincrona.
- A referencia MMA 2021 em CSV e operacional/provisoria para desenvolvimento do pipeline; antes da gold final, validar contra as portarias MMA vigentes.
- Para a primeira versao operacional, foi decidido usar MMA Dados Abertos 2021 como referencia da gold.

## Download assincrono GBIF

Este fluxo deve ser usado para volumes grandes de ocorrencias.

Em vez de buscar pagina por pagina na API publica, o projeto envia um pedido ao GBIF.
O GBIF prepara um arquivo compactado nos servidores dele e devolve uma chave chamada `download_key`.
Quando o status do pedido estiver `SUCCEEDED`, o projeto baixa o ZIP oficial para o bronze.

Credenciais:

```powershell
$env:GBIF_USERNAME="usuario_gbif"
$env:GBIF_PASSWORD="senha_gbif"
$env:GBIF_EMAIL="email_da_conta"
```

As credenciais devem ficar apenas em variaveis de ambiente.
A senha nunca deve ser salva em codigo, documentacao, manifest ou arquivo de configuracao.

### 1. Preparar o pedido sem enviar

Este comando gera o JSON do pedido para revisao.
Ele nao envia nada ao GBIF.

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download prepare --date YYYYMMDD
```

Saida esperada:

```text
data/gbif/01_bronze/occurrence/YYYYMMDD/download_requests/
|-- threatened_species_occurrence_download_request.json
`-- threatened_species_occurrence_download_manifest.json
```

Por padrao, o pedido usa:

- `COUNTRY = BR`
- `TAXON_KEY` das especies reconciliadas entre MMA e GBIF
- `OCCURRENCE_STATUS = PRESENT`
- formato `DWCA`

`OCCURRENCE_STATUS = PRESENT` significa que o download traz apenas registros em que a especie foi registrada como presente no local.
Registros `ABSENT`, quando existem, indicam que houve busca ou amostragem, mas a especie nao foi encontrada.
Eles nao entram por padrao porque a primeira gold tem foco em ocorrencias de presenca de especies ameacadas no Brasil.

Para incluir registros de ausencia em uma analise futura, usar:

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download prepare --date YYYYMMDD --include-absent
```

### 2. Enviar o pedido ao GBIF

Este comando autentica com a conta GBIF e envia o pedido.
O retorno principal e o `download_key`.

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download submit --date YYYYMMDD
```

Tambem e possivel enviar um pedido ja preparado:

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download submit --date YYYYMMDD --request-file data/gbif/01_bronze/occurrence/YYYYMMDD/download_requests/threatened_species_occurrence_download_request.json
```

### 3. Consultar o status

Trocar `<download_key>` pela chave retornada pelo GBIF.

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download status --date YYYYMMDD --download-key <download_key>
```

Status comuns:

- `PREPARING`: o GBIF ainda esta preparando o arquivo
- `SUCCEEDED`: o arquivo esta pronto para baixar
- `KILLED` ou `FAILED`: o pedido falhou ou foi interrompido

### 4. Baixar o ZIP quando estiver pronto

Executar apenas quando o status for `SUCCEEDED`.

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download download --date YYYYMMDD --download-key <download_key>
```

Saida esperada:

```text
data/gbif/01_bronze/occurrence/YYYYMMDD/downloads/<download_key>.zip
data/gbif/01_bronze/occurrence/YYYYMMDD/downloads/<download_key>_download_manifest.json
```

Depois do ZIP no bronze, os proximos passos sao transformar esse arquivo para silver e gerar a gold.

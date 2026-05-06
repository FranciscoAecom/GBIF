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
uv run python -m src.gbif.gold.build_threatened_species_occurrences --date YYYYMMDD --download-key <download_key>
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
- O pedido completo usa os `TAXON_KEY` reconciliados entre MMA e GBIF apenas quando o match representa taxon de especie, subespecie ou variedade.
- Matches amplos como `HIGHERRANK` ou `NONE` nao entram no pedido padrao, porque podem trazer descendentes demais e incluir registros que nao correspondem diretamente a especies ameacadas da lista MMA.
- Limites opcionais devem ficar restritos a testes controlados ou diagnosticos tecnicos.
- `build_threatened_species_occurrences` gera `occurrences.json` lendo o `occurrence.txt` dentro do ZIP DWCA oficial baixado do GBIF e mantem apenas ocorrencias ligadas a um `species_id` da referencia MMA.
- `build_threatened_species_datasets` gera `datasets.json` a partir dos `dataset_key` observados nas ocorrencias e metadados publicos do GBIF, lendo `occurrences.json` em streaming.
- `build_threatened_species_geopackage` gera `threatened_species_occurrences.gpkg` com ocorrencias georreferenciadas em `EPSG:4326`, gravando em lotes para suportar volumes grandes.
- Para carga grande de ocorrencias, usar a Download API assincrona.
- A referencia MMA 2021 em CSV e a referencia operacional da primeira versao; antes da gold final normativa, validar contra as portarias MMA vigentes.
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
- `TAXON_KEY` das especies, subespecies e variedades reconciliadas entre MMA e GBIF
- `OCCURRENCE_STATUS = PRESENT`
- formato `DWCA`

O pedido nao deve incluir matches `HIGHERRANK` ou `NONE`.
Esses casos significam que o GBIF nao encontrou a especie exata e retornou um nivel mais amplo, como genero, classe ou filo.
Para o produto de especies ameacadas, usar esses niveis amplos pode trazer muitas ocorrencias de organismos relacionados, mas que nao sao necessariamente a especie ameacada da lista MMA.

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

Se a conexao cair durante o download, executar o mesmo comando novamente.
O pipeline tenta retomar o arquivo parcial:

- preserva o progresso em `.zip.part`
- usa HTTP `Range` quando o servidor permite
- tenta ate 5 vezes por padrao
- ao concluir, renomeia o parcial para `.zip`

Para alterar o numero de tentativas:

```powershell
uv run python -m src.gbif.occurrence.bronze.async_threatened_occurrence_download download --date YYYYMMDD --download-key <download_key> --max-attempts 10
```

Depois do ZIP no bronze, o produto `threatened_species_brazil` gera `occurrences.json` diretamente a partir do `occurrence.txt` do DWCA oficial.
Os passos seguintes leem `occurrences.json` de forma incremental para gerar `datasets.json` e o GeoPackage.

O GeoPackage usa as coordenadas ACM (`acm_decimal_latitude` e `acm_decimal_longitude`) e aplica filtros adicionais:

- latitude e longitude precisam ser validas
- registros com alerta geoespacial do GBIF sao descartados
- pontos fora da caixa aproximada do Brasil sao descartados
- pontos possivelmente invertidos sao exportados com latitude/longitude corrigidas nos campos ACM e `acm_coordinate_was_swapped = true`

Caixa aproximada usada:

```text
latitude:  -34 a 6
longitude: -74 a -28
```

# Especies Ameacadas no Brasil

## Decisao

O produto analitico prioritario do projeto sera uma base `gold` de especies ameacadas no Brasil.

Pasta prevista:

```text
data/gbif/03_gold/threatened_species_brazil/
```

## Objetivo

Montar uma base final que permita analisar especies ameacadas no Brasil a partir da combinacao de:

- dados taxonomicos
- ocorrencias no territorio brasileiro
- datasets de origem
- referencia oficial de ameaca

## Metodo

A lista MMA e a referencia para dizer quais especies sao ameacadas no Brasil.
O GBIF entra para encontrar e organizar os dados relacionados a essas especies.

Frase-guia do metodo:

```text
Vamos usar a lista MMA como referencia oficial de especies ameacadas,
cruzar essas especies com dados GBIF em checklist, occurrence, metadata
e, opcionalmente, sampling_event, e entao gerar a gold.
```

Fluxo metodologico:

1. Referencia oficial
   - Ler a lista MMA de especies ameacadas do Brasil.
   - Preservar a fonte oficial, documento, ano e categoria de ameaca.
   - Manter todas as categorias observadas na referencia oficial usada.
   - Filtros por categoria, quando necessarios, devem ser aplicados como recorte analitico posterior e nao como exclusao da referencia base.
   - Script previsto: `src.gbif.reference.threatened_species_brazil.download_official_reference`.
   - Script previsto: `src.gbif.reference.threatened_species_brazil.build_reference`.

2. Taxonomia e nomes
   - Procurar essas especies no GBIF `checklist`.
   - Resolver nomes, sinonimos, `taxon_key` e `accepted_taxon_key`.
   - Registrar o status e a confianca do pareamento taxonomico.
   - Script previsto: `src.gbif.reference.threatened_species_brazil.reconcile_gbif_taxonomy`.
   - Script previsto: `src.gbif.reference.threatened_species_brazil.apply_gbif_taxonomy_matches`.

3. Ocorrencias
   - Buscar no GBIF `occurrence` registros dessas especies no Brasil.
   - Preservar localidade, data, coordenadas, dataset de origem e licenca.
   - Manter ocorrencias sem coordenada em `occurrences.json`, mesmo que elas nao entrem no GeoPackage.
   - Script inicial sem conta: `src.gbif.occurrence.bronze.extract_threatened_occurrences`.
   - Para carga grande, usar Download API assincrona do GBIF quando houver conta.

4. Metadados
   - Identificar em `metadata` os datasets GBIF que forneceram esses registros.
   - Preservar titulo, tipo, organizacoes, DOI, licenca, homepage e citacao.

5. Sampling event
   - Quando disponivel, enriquecer ocorrencias com protocolo, metodo e esforco de amostragem.
   - Tratar `sampling_event` como enriquecimento opcional, nao como requisito do MVP.

6. Gold
   - Gerar a base final em `data/gbif/03_gold/threatened_species_brazil/`.
   - Produzir arquivos relacionais JSON, saida espacial GeoPackage e artefatos de controle.

Papel de cada classe GBIF:

```text
checklist
= ajuda a reconciliar nomes e taxonomia

occurrence
= traz os registros das especies no Brasil

metadata
= descreve os datasets de origem

sampling_event
= enriquece ocorrencias com metodo e esforco, quando existir
```

Saida final esperada:

```text
data/gbif/03_gold/threatened_species_brazil/
|-- species.json
|-- occurrences.json
|-- datasets.json
|-- threatened_species_occurrences.gpkg
|-- schema.json
|-- quality_report.json
`-- manifest.json
```

## Fonte Principal de Ameaca

A fonte principal deve ser a lista oficial brasileira:

- MMA / Lista Nacional Oficial de Especies Ameacadas

Essa escolha foi feita porque o produto tem recorte nacional brasileiro. A lista nacional e mais adequada do que iniciar pela IUCN quando a pergunta e sobre especies ameacadas no Brasil.

## Fonte Operacional Provisoria

Para iniciar o desenvolvimento do pipeline, foi usada a base tabular do MMA disponivel no Portal de Dados Abertos:

```text
MMA Dados Abertos - Especies Ameacadas
FAUNA - Lista de Especies Ameacadas - 2021.csv
FLORA - Lista de Especies Ameacadas - 2021.csv
```

Justificativa:

- os arquivos estao em CSV, portanto permitem leitura automatizada e reprodutivel
- as colunas trazem nomes cientificos, grupos/familias e categorias
- a estrutura tabular permite desenvolver e testar o pipeline de referencia, reconciliacao taxonomica e cruzamento com GBIF
- os arquivos sao publicados no portal oficial de dados abertos do MMA

Limite dessa escolha:

- essa base 2021 e uma referencia operacional para desenvolvimento
- ela nao deve ser tratada como a versao normativa final mais atualizada da lista nacional
- a `gold` final deve registrar claramente qual ato normativo vigente foi usado como fonte oficial

Decisao para a primeira versao operacional:

- usar os CSVs MMA Dados Abertos 2021 como fonte de referencia da primeira versao da `gold`
- tratar portarias posteriores como melhoria futura ou etapa de validacao posterior
- registrar essa decisao no `manifest.json` da `gold`

## Fonte Normativa Final

Antes da publicacao da `gold` final, a referencia de ameaca deve ser validada e, se necessario, substituida ou complementada pelos atos normativos mais recentes do MMA.

Atos normativos a considerar:

- Portaria MMA nº 148/2022
- Portaria MMA nº 300/2022
- Portaria MMA nº 354/2023
- atualizacoes posteriores publicadas pelo MMA, incluindo listas especificas por grupo quando existirem

Regra:

- a base CSV 2021 pode ser usada para desenvolvimento do pipeline
- a base final deve usar a lista oficial vigente ou documentar explicitamente por que uma versao anterior foi mantida
- quando a fonte normativa estiver em PDF/anexo legal, sera necessario criar uma etapa de conversao/curadoria para transforma-la em tabela de referencia
- o `manifest.json` da `gold` deve registrar a fonte normativa exata, URL, documento, data e versao

## Fontes de Apoio

Para enriquecer e validar a referencia principal:

- ICMBio para fauna
- CNCFlora/JBRJ para flora

## Fonte Complementar

A IUCN pode ser usada como complemento quando houver necessidade de comparar:

- status nacional no Brasil
- status global

A IUCN nao deve substituir a lista nacional como fonte principal do produto.

## Entradas Esperadas

GBIF:

```text
data/gbif/02_silver/checklist/
data/gbif/02_silver/occurrence/
data/gbif/02_silver/metadata/
data/gbif/02_silver/sampling_event/  <-- opcional para enriquecer metodo, protocolo e esforco de amostragem
```

Referencia de ameaca:

```text
data/gbif/00_reference/threatened_species_brazil/
```

Arquivos de referencia gerados no fluxo inicial:

```text
data/gbif/00_reference/threatened_species_brazil/official_reference_manifest.json
data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference.json
data/gbif/00_reference/threatened_species_brazil/gbif_taxonomy_matches.json
data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json
```

## Saidas Previstas

```text
data/gbif/03_gold/threatened_species_brazil/species.json
data/gbif/03_gold/threatened_species_brazil/occurrences.json
data/gbif/03_gold/threatened_species_brazil/datasets.json
data/gbif/03_gold/threatened_species_brazil/threatened_species_occurrences.gpkg
data/gbif/03_gold/threatened_species_brazil/schema.json
data/gbif/03_gold/threatened_species_brazil/quality_report.json
data/gbif/03_gold/threatened_species_brazil/manifest.json
```

## Por que separar em tres arquivos

A base `threatened_species_brazil` separa especies, ocorrencias e datasets porque cada arquivo tem uma unidade de analise diferente.

```text
species.json
= uma linha por especie ameacada

occurrences.json
= uma linha por ocorrencia GBIF dessa especie no Brasil

datasets.json
= uma linha por dataset GBIF que forneceu ocorrencias
```

Essa separacao evita repeticao desnecessaria. Uma unica especie ameacada pode ter muitas ocorrencias GBIF, vindas de muitos datasets diferentes.

Exemplo conceitual:

```text
1 especie ameacada
pode ter
10.000 ocorrencias GBIF
vindas de
50 datasets diferentes
```

Se tudo fosse salvo em um unico arquivo, os dados da especie e do dataset seriam repetidos em milhares de linhas de ocorrencia.

Modelo resumido:

```text
species.json
species_id | scientific_name | threat_status_br

occurrences.json
gbif_id | species_id | lat | lon | date | dataset_key

datasets.json
dataset_key | dataset_title | license | citation
```

Relacionamentos:

```text
species.species_id -> occurrences.species_id
datasets.dataset_key -> occurrences.dataset_key
```

Leitura:

- `species.json` responde quais especies ameacadas entram na base.
- `occurrences.json` responde onde e quando essas especies aparecem no GBIF dentro do Brasil.
- `datasets.json` responde quais bases GBIF sustentam essas ocorrencias.

## Saida Espacial

A base `threatened_species_brazil` tambem deve gerar um GeoPackage para visualizacao em SIG:

```text
data/gbif/03_gold/threatened_species_brazil/threatened_species_occurrences.gpkg
```

Objetivo:

- permitir visualizar em mapa as ocorrencias georreferenciadas das especies ameacadas no Brasil
- abrir diretamente em QGIS, ArcGIS ou ferramentas compativeis com GeoPackage

Regra de formacao:

- o GeoPackage deve ser derivado de `occurrences.json`
- cada feicao representa uma ocorrencia GBIF georreferenciada
- `decimal_longitude` deve ser usado como coordenada X
- `decimal_latitude` deve ser usado como coordenada Y
- o sistema de coordenadas deve ser `EPSG:4326`
- somente ocorrencias com latitude e longitude validas entram no `.gpkg`
- ocorrencias sem coordenadas continuam preservadas em `occurrences.json`

Campos minimos no GeoPackage:

```text
record_id
gbif_id
species_id
scientific_name
threat_status_br
taxon_key
dataset_key
basis_of_record
occurrence_status
event_date
country_code
state_province
municipality
locality
decimal_latitude
decimal_longitude
coordinate_uncertainty_in_meters
has_geospatial_issue
license
references
```

Observacoes:

- `threat_status_br` deve vir do relacionamento com `species.json`.
- `dataset_key` permite ligar a feicao espacial a `datasets.json`.
- O `.gpkg` e uma saida de consumo espacial, nao substitui os arquivos JSON relacionais.
- Arquivos `.gpkg` da camada `gold` devem ser versionados via Git LFS.

## Campos Canonicos

### `species.json`

Unidade de registro: uma especie ameacada no Brasil.

```text
species_id
scientific_name
canonical_name
accepted_scientific_name
taxon_rank
taxon_key
accepted_taxon_key
kingdom
phylum
class
order
family
genus
species
threat_status_br
threat_status_br_code
threat_status_br_source
threat_status_br_source_document
threat_status_br_year
threat_status_global
threat_status_global_source
is_endemic_to_brazil
biome
state_occurrence
source_reference_path
gbif_checklist_match_status
gbif_taxon_match_confidence
snapshot_date
```

Descricoes:

- `species_id`: identificador interno do produto gold para a especie.
- `scientific_name`: nome cientifico conforme a referencia de ameaca.
- `canonical_name`: nome canonico sem autoria quando disponivel.
- `accepted_scientific_name`: nome aceito apos reconciliacao taxonomica.
- `taxon_rank`: nivel taxonomico do registro, como especie, subespecie ou variedade.
- `taxon_key`: chave GBIF associada ao nome usado.
- `accepted_taxon_key`: chave GBIF do taxon aceito.
- `kingdom`: reino taxonomico.
- `phylum`: filo ou divisao taxonomica.
- `class`: classe taxonomica.
- `order`: ordem taxonomica.
- `family`: familia taxonomica.
- `genus`: genero taxonomico.
- `species`: binomio especifico aceito ou observado, quando disponivel.
- `threat_status_br`: categoria de ameaca nacional em texto.
- `threat_status_br_code`: codigo da categoria nacional, como `VU`, `EN`, `CR`, `RE` ou equivalente observado.
- `threat_status_br_source`: instituicao/fonte da categoria nacional.
- `threat_status_br_source_document`: documento legal ou tecnico de origem.
- `threat_status_br_year`: ano da referencia nacional usada.
- `threat_status_global`: categoria global, quando enriquecida por fonte complementar.
- `is_endemic_to_brazil`: indicador de endemismo no Brasil quando houver fonte confiavel.
- `biome`: biomas associados quando a referencia trouxer esse recorte.
- `state_occurrence`: UFs ou regioes de ocorrencia indicadas pela referencia.
- `source_reference_path`: caminho do arquivo de referencia usado.
- `gbif_checklist_match_status`: status do pareamento com taxonomia GBIF.
- `gbif_taxon_match_confidence`: confianca do pareamento taxonomico, quando disponivel.
- `snapshot_date`: data de geracao ou referencia do produto gold.

### `occurrences.json`

Unidade de registro: uma ocorrencia GBIF no Brasil associada a uma especie ameacada.

```text
record_id
gbif_id
species_id
scientific_name
taxon_key
dataset_key
basis_of_record
occurrence_status
event_date
year
month
day
country_code
state_province
municipality
locality
decimal_latitude
decimal_longitude
coordinate_uncertainty_in_meters
has_coordinate
has_geospatial_issue
sampling_event_id
sampling_protocol
sampling_effort
license
references
snapshot_date
bronze_file_path
```

Descricoes:

- `record_id`: identificador unico do registro no produto gold.
- `gbif_id`: identificador original da ocorrencia no GBIF.
- `species_id`: chave de ligacao com `species.json`.
- `scientific_name`: nome cientifico associado a ocorrencia no GBIF.
- `taxon_key`: chave GBIF do taxon associado a ocorrencia.
- `dataset_key`: dataset GBIF de origem.
- `basis_of_record`: tipo do registro, como especime preservado, observacao humana ou outro.
- `occurrence_status`: status da ocorrencia, geralmente presenca ou ausencia quando informado.
- `event_date`: data da ocorrencia.
- `year`: ano da ocorrencia.
- `month`: mes da ocorrencia.
- `day`: dia da ocorrencia.
- `country_code`: deve ser `BR` para este produto.
- `state_province`: estado, provincia ou regiao administrativa informada no registro.
- `municipality`: municipio informado no registro.
- `locality`: descricao textual da localidade.
- `decimal_latitude`: latitude decimal da ocorrencia quando disponivel.
- `decimal_longitude`: longitude decimal da ocorrencia quando disponivel.
- `coordinate_uncertainty_in_meters`: incerteza da coordenada em metros quando informada.
- `has_coordinate`: indicador de existencia de coordenada no registro quando informado pelo GBIF.
- `has_geospatial_issue`: indicador de problema geografico informado pelo GBIF.
- `sampling_event_id`: identificador do evento de amostragem associado, quando disponivel.
- `sampling_protocol`: protocolo ou metodo de amostragem, quando disponivel em `sampling_event`.
- `sampling_effort`: esforco de amostragem, quando disponivel em `sampling_event`.
- `license`: licenca de uso do registro ou dataset de origem.
- `references`: URL ou referencia publica associada a ocorrencia.
- `snapshot_date`: data de geracao ou referencia do produto gold.
- `bronze_file_path`: rastreabilidade ate o bruto usado na transformacao.

### `datasets.json`

Unidade de registro: um dataset GBIF que contribuiu com registros de especies ameacadas.

```text
dataset_key
dataset_title
dataset_type
publishing_org_key
hosting_org_key
doi
license
homepage
citation
record_count_total
threatened_species_record_count
threatened_species_count
source_occurrence_count
snapshot_date
bronze_file_path
```

Descricoes:

- `dataset_key`: chave GBIF do dataset.
- `dataset_title`: titulo do dataset.
- `dataset_type`: classe/tipo do dataset no GBIF.
- `publishing_org_key`: organizacao publicadora.
- `hosting_org_key`: organizacao hospedadora.
- `doi`: DOI do dataset quando informado.
- `license`: licenca de uso do dataset.
- `homepage`: pagina publica do dataset quando informada.
- `citation`: citacao recomendada para uso do dataset.
- `record_count_total`: quantidade total de registros do dataset quando conhecida.
- `threatened_species_record_count`: quantidade de ocorrencias de especies ameacadas vindas desse dataset.
- `threatened_species_count`: quantidade de especies ameacadas distintas representadas nesse dataset.
- `source_occurrence_count`: quantidade de ocorrencias GBIF usadas como fonte para o produto.
- `snapshot_date`: data de geracao ou referencia do produto gold.
- `bronze_file_path`: rastreabilidade ate o bruto usado na transformacao.

## Regras

- A `gold` deve nascer das camadas `silver` e das referencias oficiais, nao diretamente do `bronze`.
- O `bronze` continua preservado para rastreabilidade.
- O `manifest.json` deve registrar todos os snapshots e referencias usados.
- Campos sem origem confiavel devem ficar nulos.
- A base nao deve inferir status de ameaca sem uma referencia explicita.
- Os campos canonicos acima formam o contrato inicial da base, mas podem evoluir com documentacao explicita.

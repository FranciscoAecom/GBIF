# Threatened Species Brazil References

Esta pasta deve guardar as referencias oficiais e auxiliares usadas para montar a base `gold` de especies ameacadas no Brasil.

Fonte principal:

- MMA / Lista Nacional Oficial de Especies Ameacadas

Fonte operacional da primeira versao:

- MMA Dados Abertos - Especies Ameacadas
- FAUNA - Lista de Especies Ameacadas - 2021.csv
- FLORA - Lista de Especies Ameacadas - 2021.csv

Justificativa:

- arquivos em CSV
- fonte oficial de dados abertos do MMA
- formato adequado para desenvolver e testar o pipeline

Limite:

- a versao final da `gold` deve ser validada contra a lista normativa vigente, como Portaria MMA nº 148/2022 e atualizacoes posteriores

Decisao da primeira versao:

- usar os CSVs MMA Dados Abertos 2021 como referencia da primeira versao operacional da gold
- manter portarias posteriores como melhoria/validacao futura

## Normalizacao

A normalizacao transforma os CSVs brutos de fauna e flora em uma tabela padronizada do projeto.

Ela:

- le os arquivos de fauna e flora de 2021
- identifica nome cientifico, familia, ordem e grupo taxonomico
- separa a categoria de ameaca em texto e codigo
- cria um `species_id` interno
- preserva arquivo e linha de origem
- remove duplicidades evidentes

Saida gerada:

```text
threatened_species_brazil_reference.json
```

Essa saida e a referencia limpa usada para reconciliar nomes e taxonomia com o GBIF.

Fontes de apoio:

- ICMBio para fauna
- CNCFlora/JBRJ para flora
- IUCN como complemento comparativo, quando necessario

![Databricks Anti-Fraud Data Platform](img/capa.png)

# Databricks Anti-Fraud Data Platform

Projeto **acadêmico** de Engenharia de Dados que implementa uma plataforma de processamento de transações de cartão de crédito com **Python, Databricks e Delta Lake**. Utiliza arquitetura **Lakehouse em camadas (Bronze → Silver → Gold)**, ingestão incremental com **Auto Loader**, transformações com **PySpark**, armazenamento em Databricks Volumes e orquestração com 
**Databricks Jobs**. Toda a infraestrutura é provisionada e gerenciada com Terraform.

> O foco principal está no pipeline dentro do **Databricks**. A infraestrutura é criada, testada e destruída.

## Arquitetura

```mermaid
flowchart TD

    A[Kaggle<br/>CSV] --> B[Python<br/>Kaggle API]
    B --> C[Databricks Volume<br/>Landing]
    C --> D[Auto Loader<br/>Processamento incremental]
    D --> E[(Bronze<br/>transactions)]
    E --> F[PySpark<br/>Transformações]
    F --> G[(Silver<br/>transactions)]
    G --> H[PySpark<br/>Agregações]
    H --> I[(Gold<br/>transactions)]
    J[Databricks Jobs<br/>Workflow]
    
    J --> B
    J --> D
    J --> F
    J --> H

    K[Terraform]
    
    K -. Provisiona .-> C
    K -. Provisiona .-> J
    K -. Provisiona .-> E
    K -. Provisiona .-> G
    K -. Provisiona .-> I
```


| Etapa | Papel | Onde está no projeto |
|---|---|---|
| 🐍 **Python** | Consulta o Kaggle, baixa arquivos novos e envia para o Databricks | `src/upload.py` |
| 📥 **Kaggle** | Fonte dos CSVs de transações | `src/upload.py` |
| 📦 **Databricks Volumes** | Armazena os arquivos na camada Landing | `terraform/main.tf` |
| 🔄 **Auto Loader** | Ingestão incremental dos arquivos → Bronze | `src/bronze/ingest_transactions.py` |
| 🥉 **Bronze** | Dados brutos ingeridos + metadados | `src/bronze/ingest_transactions.py` |
| 🥈 **Silver** | Dados tratados, validados e tipados | `src/silver/transform_transactions.py` |
| 🥇 **Gold** | Agregações por banco/mês e métricas analíticas | `src/gold/aggregate_transactions.py` |
| ⚙️ **Databricks Jobs** | Orquestra as etapas `upload → bronze → silver → gold` | `terraform/main.tf` |
| 🏗️ **Terraform** | Provisiona e gerencia a infraestrutura do pipeline | `terraform/main.tf` |
| 🔐 **Secrets** | Armazena o token do Kaggle utilizado pelo Job | `terraform/main.tf` |


## Filosofia: criar, testar e destruir

```mermaid
flowchart LR
    A[Infra inexistente] --> B[Criar ambiente]
    B --> C[Executar pipeline]
    C --> D[Testes / demonstração]
    D --> E[Destruir infraestrutura]
    E --> F[Evitar consumo<br/>desnecessário de recursos]
```

Por ser um projeto acadêmico, o ambiente é criado rapidamente para uma demonstração e removido logo em seguida. Terraform e os scripts Python cuidam disso.

### Observacão

Este projeto foi configurado para funcionar em diferentes ambientes, permitindo sua execução tanto diretamente no **Windows** quanto através de um **Dev Container** (Linux).

## Configurando o Ambiente 

### No Dev Container:

No devcontainer todo o ambiente já esta configurado, você só precisa **configurar as credenciais no dotenv** necessárias para rodar e então realizar as configurações abaixo:

1. Pegar as variáveis do .env e colocá-las como variáveis de ambiente do terminal atual.

```bash
set -a
source .env
set +a
```

2. Verificar de forma segura se a variável KAGGLE_API_TOKEN existe e não está vazia sem mostrar o token.

```bash
echo ${KAGGLE_API_TOKEN:+CONFIGURADO}
```

3. Realizar uma cópia da variável KAGGLE_API_TOKEN para outra variável chamada TF_VAR_kaggle_api_token.

```bash
export TF_VAR_kaggle_api_token="$KAGGLE_API_TOKEN"
```

4. Verificar de forma segura se a variável TF_VAR_kaggle_api_token existe e não está vazia sem mostrar o token.

```bash
echo ${TF_VAR_kaggle_api_token:+CONFIGURADO}
```

### No Windows: 

1. Script PowerShell para Windows que lê o .env e transforma cada variável dele em uma variável de ambiente do Windows.

```bash
Get-Content .env | ForEach-Object {
     if ($_ -match '^([^#][^=]*)=(.*)$') {
         [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
     }
 }
```

2. Realizar uma cópia da variável KAGGLE_API_TOKEN para outra variável chamada TF_VAR_kaggle_api_token.

```bash
$env:TF_VAR_kaggle_api_token = $env:KAGGLE_API_TOKEN
```


## Executando

1. Acessar a pasta terraform com:

```bash
cd terraform/
```

>Se for a primeira vez execute: (Ignore se não for a primeira vez)

```bash
terraform init 
```

2. Execute dentro da pasta terraform o comando:
```bash
terraform apply -auto-approve 
```

Após a execução do Terraform, o lab estará provisionado e disponível no Databricks. Para visualizar o pipeline em funcionamento, acesse **Jobs & Pipelines** e execute o Job `anti-fraud-pipeline`. O workflow irá consultar os dados disponíveis no Kaggle, realizar a ingestão e o processamento dos arquivos e, ao final, alimentar as camadas **Bronze, Silver e Gold**.

## CONSUMO DATABRICKS

Após executar o pipeline, é possível consultar o consumo de DBUs gerado pelo Job
e estimar o custo da execução.

O Databricks registra o consumo na tabela `system.billing.usage`. Como o objetivo
deste projeto é comparar o custo de processamento entre Databricks e Snowflake,
o consumo é relacionado ao preço atual da SKU utilizada pelo Job.

A consulta abaixo:

- identifica as execuções do Job `anti-fraud-pipeline`;
- apresenta a data e hora de início e término de cada execução;
- soma os DBUs consumidos;
- obtém o preço atual do DBU através de `system.billing.list_prices`;
- calcula uma estimativa do custo em USD.

O preço utilizado é o preço mais recente registrado para a SKU
`PREMIUM_JOBS_SERVERLESS_COMPUTE_US_EAST_OHIO`. Dessa forma, o cálculo representa
quanto o consumo registrado custaria considerando o preço atual do DBU.

> **Importante:** o consumo de billing pode levar algum tempo para aparecer no
> `system.billing.usage`. Portanto, uma execução recém-finalizada pode não estar
> disponível imediatamente para consulta.

```sql
with cte_list_price as
(
select
    sku_name,
    cloud,
    pricing.default AS price_per_dbu,
    price_start_time,
    price_end_time
from system.billing.list_prices
where sku_name = 'PREMIUM_JOBS_SERVERLESS_COMPUTE_US_EAST_OHIO'
qualify row_number() over (partition by sku_name order by price_start_time desc) = 1
)
select
    usage_metadata.job_id,
    usage_metadata.job_name,
    usage_metadata.job_run_id,
    usage_start_time,
    usage_end_time,
    usage.sku_name,
    usage_unit,
    sum(usage_quantity) AS total_usage,
    list_price.price_per_dbu price_per_dbu,
    sum(usage_quantity) * list_price.price_per_dbu consume 
from system.billing.usage usage
left join cte_list_price list_price on usage.sku_name = list_price.sku_name
where usage_metadata.job_name = 'anti-fraud-pipeline'
group by all
order by total_usage desc;

```

### BENCHMARK DE CONSUMO

Para este projeto foram realizadas três execuções para avaliar o consumo do
Databricks em diferentes cenários:

1. **Execução inicial completa:** processamento de todos os arquivos disponíveis
   no dataset do Kaggle.
2. **Primeira execução incremental:** processamento de arquivos adicionados
   posteriormente.
3. **Segunda execução incremental:** novo processamento considerando arquivos
   adicionados posteriormente.

Os valores de consumo obtidos foram:

| Execução | Cenário | DBU | Preço por DBU | Custo estimado | Custo mensal estimado (Custo de cada execução * 30) |
|---|---|---:|---:|---:|---:|
| 1 | Carga inicial completa | `0.517036357142857143` | `0.350000000000000000` | `US$ 0.180963` | `US$ 5.428890` |
| 2 | Incremental | `0.248338521428571429` | `0.350000000000000000` | `US$ 0.086918` | `US$ 2.607540` |
| 3 | Incremental | `0.248338521428571429` | `0.350000000000000000` | `US$ 0.086918` | `US$ 2.607540` |

Considerando os valores observados nas três execuções, podemos estimar o custo
de processamento para um período de 30 dias.

Para isso, considera-se a execução inicial como um custo único e as duas
execuções incrementais como uma aproximação do consumo diário:

**Custo estimado em 30 dias = Execução inicial + (Incremental 1 + Incremental 2) × 30**

```text
Custo inicial:       US$ XX
Incremental 1:       US$ XX
Incremental 2:       US$ XX
--------------------------------
Consumo diário no primeiro dia:      US$ XX
Consumo diário nos demais dias:      US$ XX

Estimativa 30 dias:
US$ XX + (US$ XX × 30) = US$ XX
```

> Storage: a carga completa ocupa aproximadamente 338 MiB (0,33 GiB) no Databricks Default Storage. Durante o período de execução do benchmark, o sistema de billing registrou 0,1438794 DSU em operações de API. O workspace utilizado no projeto não apresentou registros de STORAGE_SPACE no período analisado, portanto esse componente não foi incluído no cálculo financeiro do benchmark.

## Parte 6 - Destruição da infraestrutura

Ao final da execução, não esqueça de destruir todos os artefatos no databricks.
Para isso siga os passos abaixo:

1. Garanta que você esteja em /databricks-anti-fraud-data-platform (Para voltar pastas digite o comando `cd ..`)

2. Execute o cleanup.py
```bash
uv run python /cleanup.py  
```

3. Acesse a pasta terraform novamente com `cd terraform/` e digite o comando abaixo:
```bash
terraform destroy -auto-approve
```
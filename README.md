![Databricks Anti-Fraud Data Platform](img/capa.png)

# Databricks Anti-Fraud Data Platform

Projeto **acadêmico** de engenharia de dados que demonstra um pipeline de transações de cartão com **Python + Deltalake + Databricks**, usando **arquitetura em camadas (Bronze → Silver → Gold)** e **processamento incremental** com Autoloader e Jobs.

> O foco principal está no pipeline dentro do **Databricks**. A infraestrutura é criada, testada e destruída.

No Windows: 

```bash
Get-Content .env | ForEach-Object {
     if ($_ -match '^([^#][^=]*)=(.*)$') {
         [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
     }
 }
```

```bash
$env:TF_VAR_kaggle_api_token = $env:KAGGLE_API_TOKEN
```


No Linux:
```bash
export $(grep -v '^#' .env | xargs)
```

```bash
set -a
source .env
set +a
```

```bash
echo ${KAGGLE_API_TOKEN:+CONFIGURADO}
```

```bash
export TF_VAR_kaggle_api_token="$KAGGLE_API_TOKEN"
```

```bash
echo ${TF_VAR_kaggle_api_token:+CONFIGURADO}
```
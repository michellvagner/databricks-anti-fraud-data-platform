terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

provider "databricks" {
}

data "databricks_current_user" "me" {}

resource "databricks_schema" "bronze" {
  catalog_name = "workspace"
  name         = "bronze"
}

resource "databricks_schema" "silver" {
  catalog_name = "workspace"
  name         = "silver"
}

resource "databricks_schema" "gold" {
  catalog_name = "workspace"
  name         = "gold"
}

resource "databricks_volume" "landing" {
  name         = "landing"
  catalog_name = "workspace"
  schema_name  = "bronze"
  volume_type  = "MANAGED"
  comment      = "Landing area for incoming CSV files"

  depends_on = [
    databricks_schema.bronze
  ]
}

resource "databricks_volume" "checkpoints" {
  name         = "checkpoints"
  catalog_name = "workspace"
  schema_name  = "bronze"
  volume_type  = "MANAGED"

  comment = "Checkpoint storage for Auto Loader"

  depends_on = [
    databricks_schema.bronze
  ]
}

resource "databricks_volume" "schema" {
  name         = "schema"
  catalog_name = "workspace"
  schema_name  = "bronze"
  volume_type  = "MANAGED"

  comment = "Schema metadata for Auto Loader"

  depends_on = [
    databricks_schema.bronze
  ]
}

resource "databricks_workspace_file" "bronze" {
  source = "${path.module}/../src/bronze/ingest_transactions.py"
  path   = "/Workspace/anti-fraud/bronze/ingest_transactions.py"
}

resource "databricks_workspace_file" "silver" {
  source = "${path.module}/../src/silver/transform_transactions.py"
  path   = "/Workspace/anti-fraud/silver/transform_transactions.py"
}

resource "databricks_workspace_file" "gold" {
  source = "${path.module}/../src/gold/aggregate_transactions.py"
  path   = "/Workspace/anti-fraud/gold/aggregate_transactions.py"
}

variable "kaggle_api_token" {
  type      = string
  sensitive = true
}

resource "databricks_secret_scope" "kaggle" {
  name = "anti-fraud-kaggle"
}

resource "databricks_secret" "kaggle_api_token" {
  scope        = databricks_secret_scope.kaggle.name
  key          = "api-token"
  string_value = var.kaggle_api_token
}

resource "databricks_workspace_file" "upload" {
  source = "${path.module}/../src/upload.py"
  path   = "/Workspace/anti-fraud/upload.py"
}

resource "databricks_job" "anti_fraud_pipeline" {
  name = "anti-fraud-pipeline"

  task {
    task_key = "upload"

    spark_python_task {
      python_file = databricks_workspace_file.upload.path
    }

    environment_key = "default"
  }

  task {
    task_key = "bronze"

    depends_on {
      task_key = "upload"
    }


    spark_python_task {
      python_file = databricks_workspace_file.bronze.path
    }

    environment_key = "default"
  }

  task {
    task_key = "silver"

    depends_on {
      task_key = "bronze"
    }

    spark_python_task {
      python_file = databricks_workspace_file.silver.path
    }

    environment_key = "default"
  }

  task {
    task_key = "gold"

    depends_on {
      task_key = "silver"
    }

    spark_python_task {
      python_file = databricks_workspace_file.gold.path
    }

    environment_key = "default"
  }

  environment {
    environment_key = "default"

    spec {
      client = "3"

      dependencies = [
        "kaggle",
        "databricks-sdk"
      ]
    }
  }
}
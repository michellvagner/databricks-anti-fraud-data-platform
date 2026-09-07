# %%
import os

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

# %%

load_dotenv()

TABLES = [
    "workspace.bronze.transactions",
    "workspace.silver.transactions",
    "workspace.gold.transactions",
]

#  %%
def main():
    workspace = WorkspaceClient()

    for table in TABLES:
        print(f"Removendo: {table}")

        workspace.statement_execution.execute_statement(
            warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"),
            statement=f"DROP TABLE IF EXISTS {table}",
            wait_timeout="30s",
        )

        print(f"OK: {table}")

    print("Cleanup concluído.")

# %%
if __name__ == "__main__":
    main()
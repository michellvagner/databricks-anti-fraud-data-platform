# %%
from pathlib import Path
import tempfile
import os

from kaggle.api.kaggle_api_extended import KaggleApi
from databricks.sdk import WorkspaceClient

# %%
DATASET = "vagnermichaell/card-credit-datasets-ready"
VOLUME_PATH = "/Volumes/workspace/bronze/landing"

KAGGLE_SECRET_SCOPE = "anti-fraud-kaggle"
KAGGLE_SECRET_KEY = "api-token"

# %%

def get_kaggle_token() -> str:

    # Ambiente local
    token = os.getenv("KAGGLE_API_TOKEN")

    if token:
        return token

    # Ambiente Databricks
    token = dbutils.secrets.get(
        scope=KAGGLE_SECRET_SCOPE,
        key=KAGGLE_SECRET_KEY,
    )

    return token

# %%
def get_kaggle_api() -> KaggleApi:

    token = get_kaggle_token()

    os.environ["KAGGLE_API_TOKEN"] = token

    api = KaggleApi()
    api.authenticate()

    return api

# %%
def get_kaggle_files() -> list[str]:
    api = get_kaggle_api()
    api.authenticate()

    all_files = []
    page_token = None

    while True:
        result = api.dataset_list_files(
            DATASET,
            page_size=200,
            page_token=page_token,
        )

        all_files.extend(
            file.name
            for file in result.files
            if file.name.endswith(".csv")
        )

        print(
            f"Página processada: {len(result.files)} arquivos"
        )

        next_page_token = getattr(
            result,
            "nextPageToken",
            None,
        )

        if not next_page_token:
            break

        page_token = next_page_token

    return all_files

# %%

def get_existing_files(workspace: WorkspaceClient) -> set[str]:
    return {
        file.name
        for file in workspace.files.list_directory_contents(VOLUME_PATH)
        if file.name
    }

# %%

def download_from_kaggle(
    destination: Path,
    files_to_download: list[str],
) -> None:

    if not files_to_download:
        return
    
    api = get_kaggle_api()
    api.authenticate()

    for file_name in files_to_download:
        print(f"Baixando do Kaggle: {file_name}")

        api.dataset_download_file(
            DATASET,
            file_name,
            path=str(destination),
            force=True,
            quiet=False,
        )

# %%
def upload_to_databricks(
    workspace: WorkspaceClient,
    source: Path,
    files_to_upload: list[str],
) -> None:
    

    for file_name in files_to_upload:

        local_file = source / file_name
        remote_file = f"{VOLUME_PATH}/{file_name}"

        print(f"Enviando para Databricks: {file_name}")

        workspace.files.upload_from(
            remote_file,
            str(local_file),
            overwrite=False,
        )

        print(f"OK: {remote_file}")

# %%
def main() -> None:

    workspace = WorkspaceClient()

    print("Consultando arquivos disponíveis no Kaggle...")

    kaggle_files = get_kaggle_files()

    print(f"Arquivos encontrados no Kaggle: {len(kaggle_files)}")

    existing_files = get_existing_files(workspace)

    files_to_process = [
        file_name
        for file_name in kaggle_files
        if file_name not in existing_files
    ]

    for file_name in kaggle_files:
        if file_name in existing_files:
            print(f"SKIP: {file_name} já existe no Databricks.")

    if not files_to_process:
        print("Nenhum arquivo novo para enviar.")
        return

    print(f"Arquivos novos encontrados: {len(files_to_process)}")

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        download_from_kaggle(
            temp_path,
            files_to_process,
        )

        upload_to_databricks(
            workspace,
            temp_path,
            files_to_process,
        )

    print("Pipeline de upload concluído.")

# %%

if __name__ == "__main__":
    main()
# %%

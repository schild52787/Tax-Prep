from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/taxprep.db"
    encryption_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path("./data")
    pdf_template_dir: Path = Path(__file__).resolve().parent / "pdf" / "templates"
    upload_dir: Path = Path("./data/uploads")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

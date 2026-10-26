from pathlib import Path

from app.db import get_connection
from app.repositories.import_repository import ImportRepository
from app.services.rate_import_service import RateImportService

SEED_DIRECTORY = Path(__file__).resolve().parents[1] / "seed_data"


def seed_example_data() -> None:
    carriers_path = SEED_DIRECTORY / "paqueterias.csv"
    rates_path = SEED_DIRECTORY / "tarifas.csv"

    with get_connection() as connection, connection.transaction():
        service = RateImportService(ImportRepository(connection))
        carriers = service.import_carriers(carriers_path.name, carriers_path.read_bytes())
        rates = service.import_rates(rates_path.name, rates_path.read_bytes())

    print(
        "Example data ready: "
        f"{carriers['total_rows']} carrier rows and {rates['total_rows']} rate rows processed."
    )


if __name__ == "__main__":
    seed_example_data()

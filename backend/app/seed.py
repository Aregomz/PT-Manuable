from pathlib import Path

from app.db import get_connection
from app.repositories.import_repository import ImportRepository
from app.services.historical_quote_import_service import HistoricalQuoteImportService
from app.services.rate_import_service import RateImportService

SEED_DIRECTORY = Path(__file__).resolve().parents[1] / "seed_data"


def seed_example_data() -> None:
    carriers_path = SEED_DIRECTORY / "paqueterias.csv"
    rates_path = SEED_DIRECTORY / "tarifas.csv"
    dhl_rates_path = SEED_DIRECTORY / "tarifas_dhl_v2.csv"
    historical_quotes_path = SEED_DIRECTORY / "cotizaciones_historicas.csv"

    with get_connection() as connection, connection.transaction():
        service = RateImportService(ImportRepository(connection))
        carriers = service.import_carriers(carriers_path.name, carriers_path.read_bytes())
        if not carriers["already_imported"]:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE carriers
                    SET volumetric_divisor = 5000,
                        volumetric_effective_from = DATE '2026-12-01',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE lower(name) IN ('dhl', 'fedex')
                    """
                )
        rates = service.import_rates(rates_path.name, rates_path.read_bytes())
        dhl_rates = service.import_rates(dhl_rates_path.name, dhl_rates_path.read_bytes())
        historical_quotes = HistoricalQuoteImportService(
            ImportRepository(connection)
        ).import_quotes(historical_quotes_path.name, historical_quotes_path.read_bytes())

    print(
        "Example data ready: "
        f"{carriers['total_rows']} carrier rows, "
        f"{rates['total_rows'] + dhl_rates['total_rows']} rate rows and "
        f"{historical_quotes['total_rows']} historical quotes processed."
    )


if __name__ == "__main__":
    seed_example_data()

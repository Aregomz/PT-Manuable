import csv
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


class CsvValidationError(ValueError):
    pass


EXPECTED_CARRIER_HEADERS = {"carrier_id", "nombre", "tipo_servicio", "activo"}
EXPECTED_RATE_HEADERS = {
    "paqueteria",
    "zona",
    "peso_min",
    "peso_max",
    "unidad",
    "precio",
    "dias_entrega",
    "vigencia_desde",
}
EXPECTED_RATE_V2_HEADERS = {
    "paqueteria",
    "zona",
    "peso_min_kg",
    "peso_max_kg",
    "precio_mxn",
    "dias_entrega",
    "vigencia_desde",
}

ALIASES = {
    "dhl": "dhl",
    "dhlexpress": "dhl",
    "fedex": "fedex",
    "federalexpress": "fedex",
    "estafeta": "estafeta",
    "estafetamexicana": "estafeta",
    "redpack": "redpack",
}

CANONICAL_NAMES = {
    "dhl": "DHL",
    "fedex": "FedEx",
    "estafeta": "Estafeta",
    "redpack": "Redpack",
}


def read_csv(content: bytes, expected_headers: set[str], label: str) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvValidationError(f"{label} debe estar codificado en UTF-8.") from error

    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = set(reader.fieldnames or [])
        if headers != expected_headers:
            missing = sorted(expected_headers - headers)
            extra = sorted(headers - expected_headers)
            details = []
            if missing:
                details.append(f"faltan columnas: {', '.join(missing)}")
            if extra:
                details.append(f"sobran columnas: {', '.join(extra)}")
            raise CsvValidationError(f"Estructura inválida en {label}: {'; '.join(details)}.")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    except csv.Error as error:
        raise CsvValidationError(f"No fue posible leer {label}: {error}.") from error


def read_rate_csv(content: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvValidationError(f"{label} debe estar codificado en UTF-8.") from error

    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = set(reader.fieldnames or [])
        if headers == EXPECTED_RATE_HEADERS:
            return [{key: (value or "").strip() for key, value in row.items()} for row in reader]
        if headers == EXPECTED_RATE_V2_HEADERS:
            return [
                {
                    "paqueteria": (row["paqueteria"] or "").strip(),
                    "zona": (row["zona"] or "").strip(),
                    "peso_min": (row["peso_min_kg"] or "").strip(),
                    "peso_max": (row["peso_max_kg"] or "").strip(),
                    "unidad": "kg",
                    "precio": (row["precio_mxn"] or "").strip(),
                    "dias_entrega": (row["dias_entrega"] or "").strip(),
                    "vigencia_desde": (row["vigencia_desde"] or "").strip(),
                }
                for row in reader
            ]
        raise CsvValidationError(
            f"Estructura inválida en {label}: los encabezados no corresponden "
            "al formato de tarifas soportado."
        )
    except csv.Error as error:
        raise CsvValidationError(f"No fue posible leer {label}: {error}.") from error


def normalize_carrier(
    row_number: int,
    row: dict[str, str],
    seen_codes: set[str],
) -> dict[str, Any]:
    changes: list[str] = []
    try:
        code = row["carrier_id"].strip().upper()
        raw_name = " ".join(row["nombre"].split())
        service_type = row["tipo_servicio"].strip().lower().capitalize()
        active_value = normalize_key(row["activo"])
        if not code or not raw_name or not service_type:
            return rejected(row_number, row, "La paquetería contiene campos obligatorios vacíos.")
        if code in seen_codes:
            result = rejected(row_number, row, f"El código {code} está duplicado en el archivo.")
            result["status"] = "duplicate"
            return result
        if active_value not in {"si", "no"}:
            return rejected(
                row_number, row, "El campo activo debe contener 'si' o 'no'."
            )
        canonical_key = ALIASES.get(normalize_key(raw_name), normalize_key(raw_name))
        canonical_name = CANONICAL_NAMES.get(canonical_key, raw_name)
        if row["carrier_id"] != code:
            changes.append(f"Código normalizado de '{row['carrier_id']}' a '{code}'.")
        if raw_name != canonical_name:
            changes.append(f"Nombre normalizado de '{raw_name}' a '{canonical_name}'.")
        if row["tipo_servicio"] != service_type:
            changes.append(
                f"Tipo de servicio normalizado de '{row['tipo_servicio']}' a '{service_type}'."
            )
        normalized_active = active_value == "si"
        carrier = {
            "code": code,
            "name": canonical_name,
            "service_type": service_type,
            "is_active": normalized_active,
            "canonical_key": canonical_key,
        }
        seen_codes.add(code)
        return {
            "row_number": row_number,
            "status": "corrected" if changes else "loaded",
            "raw_data": row,
            "normalized_data": {
                "carrier_id": code,
                "nombre": canonical_name,
                "tipo_servicio": service_type,
                "activo": normalized_active,
            },
            "changes": changes,
            "reason": None,
            "carrier": carrier,
            "rate": None,
        }
    except CsvValidationError as error:
        return rejected(row_number, row, str(error))


def normalize_rate(
    row_number: int,
    raw: dict[str, str],
    carrier_ids: dict[str, int],
) -> dict[str, Any]:
    changes: list[str] = []
    try:
        raw_carrier = " ".join(raw["paqueteria"].split())
        carrier_key = ALIASES.get(normalize_key(raw_carrier), normalize_key(raw_carrier))
        carrier_id = carrier_ids.get(carrier_key)
        if carrier_id is None:
            return rejected(row_number, raw, "La paquetería no existe en el catálogo cargado.")
        canonical_name = CANONICAL_NAMES.get(carrier_key, raw_carrier)
        if raw_carrier != canonical_name:
            changes.append(f"Paquetería normalizada de '{raw_carrier}' a '{canonical_name}'.")

        zone = parse_zone(raw["zona"])
        if raw["zona"] != str(zone):
            changes.append(f"Zona normalizada de '{raw['zona']}' a {zone}.")

        min_weight = parse_decimal(raw["peso_min"], "peso mínimo")
        max_weight = parse_decimal(raw["peso_max"], "peso máximo")
        unit = normalize_key(raw["unidad"])
        if unit in {"g", "gramo", "gramos"}:
            min_weight /= Decimal(1000)
            max_weight /= Decimal(1000)
            changes.append("Pesos convertidos de gramos a kilogramos.")
        elif unit in {"kg", "kgs", "kilogramo", "kilogramos"}:
            if raw["unidad"] != "kg":
                changes.append(f"Unidad normalizada de '{raw['unidad']}' a 'kg'.")
        elif not unit and max_weight <= Decimal(30):
            changes.append("Unidad vacía interpretada como kilogramos por el rango proporcionado.")
        elif not unit:
            return rejected(
                row_number,
                raw,
                "La unidad está vacía y el rango no permite determinar si está en gramos "
                "o kilogramos.",
            )
        else:
            return rejected(row_number, raw, f"Unidad de peso no reconocida: '{raw['unidad']}'.")

        if min_weight < 0 or max_weight <= min_weight:
            return rejected(
                row_number, raw, "El rango de peso es negativo, igual o está invertido."
            )

        price = parse_price(raw["precio"])
        if price <= 0:
            return rejected(row_number, raw, "El precio debe ser mayor que cero.")
        if price < Decimal(50) or price > Decimal(10000):
            return rejected(
                row_number,
                raw,
                f"El precio {price:.2f} parece atípico y requiere confirmación de Comercial.",
            )
        normalized_price_text = f"{price:.2f}"
        if raw["precio"] != normalized_price_text:
            changes.append(
                f"Precio normalizado de '{raw['precio']}' a {normalized_price_text} MXN."
            )

        min_days, max_days = parse_delivery_days(raw["dias_entrega"])
        if raw["dias_entrega"] and raw["dias_entrega"] != delivery_text(min_days, max_days):
            changes.append(f"Tiempo de entrega normalizado desde '{raw['dias_entrega']}'.")

        effective_from = parse_date(raw["vigencia_desde"])
        if effective_from and raw["vigencia_desde"] != effective_from.isoformat():
            changes.append(
                f"Vigencia normalizada de '{raw['vigencia_desde']}' a {effective_from.isoformat()}."
            )

        rate = {
            "carrier_id": carrier_id,
            "zone": zone,
            "min_weight_kg": min_weight.quantize(Decimal("0.001")),
            "max_weight_kg": max_weight.quantize(Decimal("0.001")),
            "price_mxn": price.quantize(Decimal("0.01")),
            "min_delivery_days": min_days,
            "max_delivery_days": max_days,
            "effective_from": effective_from,
        }
        normalized = {
            "paqueteria": canonical_name,
            "zona": zone,
            "peso_min_kg": str(rate["min_weight_kg"]),
            "peso_max_kg": str(rate["max_weight_kg"]),
            "precio_mxn": str(rate["price_mxn"]),
            "dias_entrega_min": min_days,
            "dias_entrega_max": max_days,
            "vigencia_desde": effective_from.isoformat() if effective_from else None,
        }
        return {
            "row_number": row_number,
            "status": "corrected" if changes else "loaded",
            "raw_data": raw,
            "normalized_data": normalized,
            "changes": changes,
            "reason": None,
            "rate": rate,
        }
    except CsvValidationError as error:
        return rejected(row_number, raw, str(error))


def rejected(row_number: int, raw: dict[str, str], reason: str) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "status": "rejected",
        "raw_data": raw,
        "normalized_data": None,
        "changes": [],
        "reason": reason,
        "rate": None,
    }


def normalize_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", without_accents)


def parse_zone(value: str) -> int:
    match = re.fullmatch(r"(?:zona|z)?\s*([0-9]+)", value.strip(), flags=re.IGNORECASE)
    if not match:
        raise CsvValidationError(f"Zona no reconocida: '{value}'.")
    zone = int(match.group(1))
    if zone not in range(1, 5):
        raise CsvValidationError(f"La zona {zone} está fuera del rango permitido (1 a 4).")
    return zone


def parse_decimal(value: str, field_name: str) -> Decimal:
    if not value:
        raise CsvValidationError(f"Falta el {field_name}.")
    try:
        return Decimal(value.replace(" ", "").replace(",", "."))
    except InvalidOperation as error:
        raise CsvValidationError(f"El {field_name} no es numérico: '{value}'.") from error


def parse_price(value: str) -> Decimal:
    if not value:
        raise CsvValidationError("La tarifa no tiene precio; requiere confirmación de Comercial.")
    cleaned = re.sub(r"(?i)mxn|\$|\s", "", value)
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as error:
        raise CsvValidationError(f"El precio no es numérico: '{value}'.") from error


def parse_delivery_days(value: str) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    numbers = [int(number) for number in re.findall(r"\d+", value)]
    if len(numbers) == 1 and numbers[0] > 0:
        return numbers[0], numbers[0]
    if len(numbers) == 2 and 0 < numbers[0] <= numbers[1]:
        return numbers[0], numbers[1]
    raise CsvValidationError(f"Tiempo de entrega no reconocido: '{value}'.")


def delivery_text(min_days: int | None, max_days: int | None) -> str:
    if min_days is None:
        return ""
    return str(min_days) if min_days == max_days else f"{min_days}-{max_days}"


def parse_date(value: str) -> date | None:
    if not value:
        return None
    spanish_months = {
        "ene": "01",
        "feb": "02",
        "mar": "03",
        "abr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dic": "12",
    }
    normalized = value.lower()
    for month, number in spanish_months.items():
        normalized = normalized.replace(month, number)
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
    raise CsvValidationError(f"Fecha de vigencia no reconocida: '{value}'.")

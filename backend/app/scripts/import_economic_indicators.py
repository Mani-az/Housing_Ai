import pandas as pd

from app.database.database import SessionLocal
from app.models.economic_indicator import EconomicIndicator


CSV_PATH = "data/economic_indicators.csv"


def clean_float(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            return None
        if value.lower() == "nan":
            return None

    try:
        return float(value)
    except ValueError:
        return None


def clean_int(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            return None
        if value.lower() == "nan":
            return None

    try:
        return int(float(value))
    except ValueError:
        return None


def clean_text(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return None

    return value


def import_economic_indicators():
    db = SessionLocal()

    try:
        df = pd.read_csv(CSV_PATH)

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            year = clean_int(row.get("year"))
            month = clean_int(row.get("month"))

            if year is None or month is None:
                skipped_count += 1
                continue

            existing_record = (
                db.query(EconomicIndicator)
                .filter(
                    EconomicIndicator.year == year,
                    EconomicIndicator.month == month,
                )
                .first()
            )

            data = {
                "general_inflation_rate": clean_float(row.get("general_inflation_rate")),

                "cpi_index": clean_float(row.get("cpi_index")),
                "cpi_yoy_growth_from_index": clean_float(row.get("cpi_yoy_growth_from_index")),

                "housing_cpi_index": clean_float(row.get("housing_cpi_index")),
                "housing_cpi_growth": clean_float(row.get("housing_cpi_growth")),

                "producer_price_index": clean_float(row.get("producer_price_index")),
                "producer_price_yoy_growth": clean_float(row.get("producer_price_yoy_growth")),

                "construction_cost_growth": clean_float(row.get("construction_cost_growth")),

                "interest_rate": clean_float(row.get("interest_rate")),

                "usd_rate_toman": clean_float(row.get("usd_rate_toman")),
                "usd_rate_irr": clean_float(row.get("usd_rate_irr")),
                "usd_growth": clean_float(row.get("usd_growth")),

                "transaction_volume": clean_float(row.get("transaction_volume")),
                "transaction_volume_growth": clean_float(row.get("transaction_volume_growth")),

                "avg_price_per_sqm_million_irr": clean_float(row.get("avg_price_per_sqm_million_irr")),
                "housing_growth_rate": clean_float(row.get("housing_growth_rate")),

                "source": clean_text(row.get("source")),
                "notes": clean_text(row.get("notes")),
            }

            if existing_record:
                for key, value in data.items():
                    setattr(existing_record, key, value)

                updated_count += 1
            else:
                indicator = EconomicIndicator(
                    year=year,
                    month=month,
                    **data,
                )

                db.add(indicator)
                imported_count += 1

        db.commit()

        print("Economic indicators import completed.")
        print(f"New rows imported: {imported_count}")
        print(f"Existing rows updated: {updated_count}")
        print(f"Rows skipped: {skipped_count}")

    except Exception as e:
        db.rollback()
        print(f"Import failed: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    import_economic_indicators()
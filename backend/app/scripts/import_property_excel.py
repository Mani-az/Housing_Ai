import pandas as pd

from app.database.database import SessionLocal
from app.models.property_listing import PropertyListing


EXCEL_PATH = "data/tehran_properties.xlsx"

# چون دیتاست برای سال 2013 است، فعلاً یک ضریب تعدیل ساده می‌گذاریم.
# بعداً می‌توانیم این را دقیق‌تر و قابل تنظیم کنیم.
DEFAULT_INFLATION_FACTOR = 12.0


def clean_float(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
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

    try:
        return int(float(value))
    except ValueError:
        return None


def import_property_excel():
    db = SessionLocal()

    try:
        df = pd.read_excel(EXCEL_PATH)

        imported_count = 0

        for _, row in df.iterrows():
            price_per_meter = clean_float(row.get("Price per Square Meter"))
            total_price = clean_float(row.get("Total Price"))

            adjusted_price_per_meter = (
                price_per_meter * DEFAULT_INFLATION_FACTOR
                if price_per_meter is not None
                else None
            )

            adjusted_total_price = (
                total_price * DEFAULT_INFLATION_FACTOR
                if total_price is not None
                else None
            )

            listing = PropertyListing(
                source_listing_id=str(row.get("ID")) if not pd.isna(row.get("ID")) else None,
                source="tehran_excel_dataset",

                submission_date=str(row.get("Submission Date")) if not pd.isna(row.get("Submission Date")) else None,

                exact_location=str(row.get("Exact Location")) if not pd.isna(row.get("Exact Location")) else None,
                neighborhood_name=str(row.get("Neighborhood Name")) if not pd.isna(row.get("Neighborhood Name")) else None,
                neighborhood_english=str(row.get("Neighborhood (English)")) if not pd.isna(row.get("Neighborhood (English)")) else None,

                base_area=clean_float(row.get("Base Area")),
                floor_level=clean_int(row.get("Floor Level")),
                building_age=clean_int(row.get("Age")),

                price_per_square_meter=price_per_meter,
                total_price=total_price,

                listing_year=clean_int(row.get("Georgian year")),

                inflation_factor=DEFAULT_INFLATION_FACTOR,
                adjusted_price_per_square_meter=adjusted_price_per_meter,
                adjusted_total_price=adjusted_total_price,
            )

            db.add(listing)
            imported_count += 1

            if imported_count % 1000 == 0:
                db.commit()
                print(f"{imported_count} rows imported...")

        db.commit()
        print(f"Import completed successfully. Total rows imported: {imported_count}")

    except Exception as e:
        db.rollback()
        print(f"Import failed: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    import_property_excel()
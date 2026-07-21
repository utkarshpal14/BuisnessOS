"""
SalesDataLoader: the only component in this feature allowed to touch the filesystem
or know about raw CSV column names.

Any future swap of the underlying Kaggle dataset should require editing COLUMN_ALIASES
below (if the new file uses different header names) and nothing else -- SalesAnalyticsService,
SalesQueryMapper, and SalesAgent all operate on the canonical schema this loader produces.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.sales.exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    SchemaValidationError,
)

# Canonical column name -> list of raw header names (any casing/spacing/punctuation)
# that should be recognized as that column. Extend this when pointing at a new dataset.
COLUMN_ALIASES: Dict[str, List[str]] = {
    "order_id": ["order_id", "orderid", "order id", "id", "invoice_id", "invoiceno", "order_number"],
    "order_date": ["order_date", "orderdate", "order date", "date", "invoice_date", "orderdt"],
    "region": ["region", "state", "area", "territory", "market"],
    "product": ["product", "product_name", "productname", "item", "category", "product_category"],
    "customer": ["customer", "customer_name", "customername", "client", "client_name", "customer_id"],
    "quantity": ["quantity", "qty", "units", "order_quantity"],
    "unit_price": ["unit_price", "unitprice", "price", "unit_cost"],
    "revenue": ["revenue", "sales", "amount", "total", "total_amount", "total_price", "sale_amount"],
}

# A row must resolve order_date + a way to compute revenue to be usable at all.
REQUIRED_CANONICAL_COLUMNS = ("order_date",)

DEFAULT_DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets" / "sales"


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


class SalesDataLoader:
    """
    Loads sales CSV(s) from a dataset directory, maps raw headers onto a canonical
    schema, cleans missing/malformed rows, and exposes a single clean DataFrame.

    Planner and agents never touch pandas or CSV files directly -- they go through this.
    """

    def __init__(self, dataset_dir: Optional[str] = None):
        self.dataset_dir = Path(dataset_dir) if dataset_dir else DEFAULT_DATASET_DIR

    def load(self) -> pd.DataFrame:
        """Returns a cleaned DataFrame with canonical columns. Raises SalesDataError subtypes on failure."""
        raw_df = self._read_csv_files()
        mapped_df = self._map_columns(raw_df)
        clean_df = self._clean(mapped_df)

        if clean_df.empty:
            raise EmptyDatasetError(
                f"Dataset at '{self.dataset_dir}' had no usable rows after cleaning."
            )
        return clean_df

    def _read_csv_files(self) -> pd.DataFrame:
        if not self.dataset_dir.exists() or not self.dataset_dir.is_dir():
            raise DatasetNotFoundError(
                f"Sales dataset directory not found: '{self.dataset_dir}'. "
                "Place a Kaggle sales CSV inside this folder."
            )

        csv_files = sorted(self.dataset_dir.glob("*.csv"))
        if not csv_files:
            raise DatasetNotFoundError(
                f"No CSV files found in '{self.dataset_dir}'. "
                "Place a Kaggle sales CSV inside this folder."
            )

        frames = []
        for csv_path in csv_files:
            try:
                frame = pd.read_csv(csv_path)
            except pd.errors.EmptyDataError:
                continue
            except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as e:
                raise SchemaValidationError(f"Failed to parse CSV '{csv_path.name}': {e}") from e

            if frame.shape[1] == 0:
                continue
            frames.append(frame)

        if not frames:
            raise EmptyDatasetError(f"All CSV files in '{self.dataset_dir}' were empty.")

        return pd.concat(frames, ignore_index=True)

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_lookup: Dict[str, str] = {}
        for canonical, aliases in COLUMN_ALIASES.items():
            normalized_aliases = {_normalize(a) for a in aliases} | {_normalize(canonical)}
            for raw_col in df.columns:
                if _normalize(raw_col) in normalized_aliases:
                    normalized_lookup[raw_col] = canonical
                    break

        renamed = df.rename(columns=normalized_lookup)
        canonical_cols_present = set(normalized_lookup.values())

        missing_required = [c for c in REQUIRED_CANONICAL_COLUMNS if c not in canonical_cols_present]
        if missing_required:
            raise SchemaValidationError(
                f"Dataset is missing required column(s) {missing_required}. "
                f"Recognized columns: {sorted(canonical_cols_present) or 'none'}. "
                "Update COLUMN_ALIASES in data_loader.py if this dataset uses different headers."
            )

        can_derive_revenue = "revenue" in canonical_cols_present or (
            "quantity" in canonical_cols_present and "unit_price" in canonical_cols_present
        )
        if not can_derive_revenue:
            raise SchemaValidationError(
                "Dataset has no 'revenue' column and no ('quantity' + 'unit_price') pair to derive it from. "
                "Update COLUMN_ALIASES in data_loader.py if this dataset uses different headers."
            )

        keep_cols = [c for c in renamed.columns if c in COLUMN_ALIASES]
        return renamed[keep_cols].copy()

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

        if "revenue" in df.columns:
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
        else:
            df["quantity"] = pd.to_numeric(df.get("quantity"), errors="coerce")
            df["unit_price"] = pd.to_numeric(df.get("unit_price"), errors="coerce")
            df["revenue"] = df["quantity"] * df["unit_price"]

        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

        # Malformed/incomplete rows: unparseable date or non-computable revenue.
        df = df.dropna(subset=["order_date", "revenue"])
        df = df[df["revenue"] >= 0]

        for optional_col in ("region", "product", "customer"):
            if optional_col in df.columns:
                df[optional_col] = df[optional_col].fillna("Unknown").astype(str).str.strip()
                df.loc[df[optional_col] == "", optional_col] = "Unknown"

        return df.reset_index(drop=True)

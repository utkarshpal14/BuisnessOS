"""
FinanceDataLoader: the only component in this feature allowed to touch the filesystem
or know about raw CSV column names. Mirrors app/sales/data_loader.py.

Any future swap of the underlying Kaggle dataset should require editing COLUMN_ALIASES
below (if the new file uses different header names) and nothing else -- FinanceAnalyticsService,
FinanceQueryMapper, and FinanceAgent all operate on the canonical schema this loader produces.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.finance.exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    SchemaValidationError,
)

# Canonical column name -> list of raw header names (any casing/spacing/punctuation)
# that should be recognized as that column. Extend this when pointing at a new dataset.
COLUMN_ALIASES: Dict[str, List[str]] = {
    "date": ["date", "transaction_date", "period", "month", "record_date", "posting_date"],
    "revenue": ["revenue", "sales", "income", "total_revenue", "gross_revenue"],
    "expenses": ["expenses", "expense", "cost", "costs", "total_expenses", "cogs", "cost_of_goods_sold"],
    "profit": ["profit", "net_profit", "net_income", "earnings"],
    "category": ["category", "expense_category", "department", "cost_center"],
    "region": ["region", "state", "area", "territory", "market"],
}

REQUIRED_CANONICAL_COLUMNS = ("date",)

DEFAULT_DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets" / "finance"


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


class FinanceDataLoader:
    """
    Loads finance CSV(s) from a dataset directory, maps raw headers onto a canonical
    schema, derives whichever of revenue/expenses/profit is missing from the other two,
    cleans missing/malformed rows, and exposes a single clean DataFrame.

    Planner and agents never touch pandas or CSV files directly -- they go through this.
    """

    def __init__(self, dataset_dir: Optional[str] = None):
        self.dataset_dir = Path(dataset_dir) if dataset_dir else DEFAULT_DATASET_DIR

    def load(self) -> pd.DataFrame:
        """Returns a cleaned DataFrame with canonical columns. Raises FinanceDataError subtypes on failure."""
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
                f"Finance dataset directory not found: '{self.dataset_dir}'. "
                "Place a Kaggle finance CSV inside this folder."
            )

        csv_files = sorted(self.dataset_dir.glob("*.csv"))
        if not csv_files:
            raise DatasetNotFoundError(
                f"No CSV files found in '{self.dataset_dir}'. "
                "Place a Kaggle finance CSV inside this folder."
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

        money_cols_present = {"revenue", "expenses", "profit"} & canonical_cols_present
        if len(money_cols_present) < 2:
            raise SchemaValidationError(
                "Dataset needs at least two of 'revenue', 'expenses', 'profit' to derive the third. "
                f"Found: {sorted(money_cols_present) or 'none'}. "
                "Update COLUMN_ALIASES in data_loader.py if this dataset uses different headers."
            )

        keep_cols = [c for c in renamed.columns if c in COLUMN_ALIASES]
        return renamed[keep_cols].copy()

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        for money_col in ("revenue", "expenses", "profit"):
            if money_col in df.columns:
                df[money_col] = pd.to_numeric(df[money_col], errors="coerce")

        if "revenue" not in df.columns:
            df["revenue"] = df["expenses"] + df["profit"]
        elif "expenses" not in df.columns:
            df["expenses"] = df["revenue"] - df["profit"]
        elif "profit" not in df.columns:
            df["profit"] = df["revenue"] - df["expenses"]

        # Malformed/incomplete rows: unparseable date or non-numeric money columns.
        df = df.dropna(subset=["date", "revenue", "expenses", "profit"])

        for optional_col in ("category", "region"):
            if optional_col in df.columns:
                df[optional_col] = df[optional_col].fillna("Unknown").astype(str).str.strip()
                df.loc[df[optional_col] == "", optional_col] = "Unknown"

        return df.reset_index(drop=True)

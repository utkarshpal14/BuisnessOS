"""
FinanceDataAccess: the only class FinanceAgent is allowed to depend on for finance
data. Mirrors app/sales/data_access.py.

Wraps FinanceDataLoader (which still does the actual CSV/pandas mechanics) behind a
role-aware gateway, so that when RBAC is implemented, it can be enforced inside this
one method -- not inside FinanceAgent, FinanceAnalyticsService, or FinanceQueryMapper,
none of which should ever need to know a caller's role.
"""
from typing import Optional

import pandas as pd

from app.finance.data_loader import FinanceDataLoader


class FinanceDataAccess:
    """Gateway between FinanceAgent and the underlying finance dataset."""

    def __init__(self, dataset_dir: Optional[str] = None):
        self._loader = FinanceDataLoader(dataset_dir=dataset_dir)

    def load(self, role: Optional[str] = None) -> pd.DataFrame:
        """
        Returns the cleaned finance DataFrame. `role` is accepted but intentionally
        not yet enforced -- no auth exists yet (see CLAUDE.md's "Deferred,
        seam-only" section). Once it does, a permission check belongs here.
        """
        return self._loader.load()

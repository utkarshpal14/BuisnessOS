"""
SalesDataAccess: the only class SalesAgent is allowed to depend on for sales data.

Wraps SalesDataLoader (which still does the actual CSV/pandas mechanics) behind a
role-aware gateway, so that when RBAC is implemented, it can be enforced inside this
one method -- not inside SalesAgent, SalesAnalyticsService, or SalesQueryMapper, none
of which should ever need to know a caller's role.
"""
from typing import Optional

import pandas as pd

from app.sales.data_loader import SalesDataLoader


class SalesDataAccess:
    """Gateway between SalesAgent and the underlying sales dataset."""

    def __init__(self, dataset_dir: Optional[str] = None):
        self._loader = SalesDataLoader(dataset_dir=dataset_dir)

    def load(self, role: Optional[str] = None) -> pd.DataFrame:
        """
        Returns the cleaned sales DataFrame. `role` is accepted but intentionally
        not yet enforced -- no auth exists yet (see CLAUDE.md's "Deferred,
        seam-only" section). Once it does, a permission check belongs here.
        """
        return self._loader.load()

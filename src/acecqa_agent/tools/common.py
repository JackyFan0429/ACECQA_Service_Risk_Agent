from __future__ import annotations

import math
from typing import Any
import pandas as pd

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import RiskThresholds, ServiceFilters


def apply_filters(df: pd.DataFrame, filters: ServiceFilters) -> pd.DataFrame:
    result = df
    if filters.state is not None:
        result = result.loc[result["state"].eq(filters.state)]
    if filters.urban_rural is not None:
        result = result.loc[result["urban_rural"].eq(filters.urban_rural)]
    if filters.service_type is not None:
        result = result.loc[result["service_type"].eq(filters.service_type)]
    if filters.overall_rating is not None:
        result = result.loc[result["overall_rating"].eq(filters.overall_rating)]
    return result.copy()


def clean_value(value: Any):
    if value is None or value is pd.NA:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def risk_thresholds() -> RiskThresholds:
    repo = get_repository()
    return RiskThresholds(
        transport_p75_km=repo.poor_access_cutoff,
        capacity_p25_places=repo.low_capacity_cutoff,
        scope="National valid Centre-Based Care analysis sample with non-missing approved places",
    )

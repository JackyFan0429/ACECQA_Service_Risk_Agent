from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    ANALYSIS_SERVICE_TYPES,
    CAPACITY_RISK_QUANTILE,
    DEFAULT_DATA_PATH,
    RISK_SERVICE_TYPE,
    TRANSPORT_QUARTILE_LABELS,
    TRANSPORT_RISK_QUANTILE,
)


def _to_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("boolean")
    mapped = series.astype("string").str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )
    return mapped.astype("boolean")


class DataRepository:
    """Loads the cleaned assignment dataset and recreates the notebook's analysis features."""

    def __init__(self, data_path: str | Path = DEFAULT_DATA_PATH):
        self.data_path = Path(data_path)
        self._df = self._load_and_prepare()
        self._analysis_df = self._build_analysis_scope()
        self._risk_df, self._poor_access_cutoff, self._low_capacity_cutoff = self._build_risk_scope()

    def _load_and_prepare(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path, low_memory=False)

        for col in ["service_type", "state", "overall_rating", "urban_rural", "sos_name"]:
            if col in df.columns:
                df[col] = df[col].astype("string").str.strip()

        for col in [
            "distance_to_train_station_km",
            "distance_to_bus_station_km",
            "number_of_approved_places",
            "longitude",
            "latitude",
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in ["valid_spatial_record", "spatial_join_success"]:
            if col in df.columns:
                df[col] = _to_bool(df[col])

        df["nearest_public_transport_km"] = df[
            ["distance_to_train_station_km", "distance_to_bus_station_km"]
        ].min(axis=1, skipna=True)
        both_missing = df[["distance_to_train_station_km", "distance_to_bus_station_km"]].isna().all(axis=1)
        df.loc[both_missing, "nearest_public_transport_km"] = np.nan
        df.loc[df["nearest_public_transport_km"] < 0, "nearest_public_transport_km"] = np.nan

        df["overall_rating_binary"] = pd.NA
        df.loc[
            df["overall_rating"].isin(["Meeting NQS", "Exceeding NQS", "Excellent"]),
            "overall_rating_binary",
        ] = "Meeting NQS or Above"
        df.loc[
            df["overall_rating"].isin(["Working Towards NQS", "Significant Improvement Required"]),
            "overall_rating_binary",
        ] = "Below Meeting NQS"

        df["below_meeting_flag"] = np.nan
        df.loc[df["overall_rating_binary"].eq("Meeting NQS or Above"), "below_meeting_flag"] = 0
        df.loc[df["overall_rating_binary"].eq("Below Meeting NQS"), "below_meeting_flag"] = 1

        return df

    def _build_analysis_scope(self) -> pd.DataFrame:
        df = self._df
        scoped = df.loc[
            df["valid_spatial_record"].fillna(False)
            & df["spatial_join_success"].fillna(False)
            & df["urban_rural"].isin(["Urban", "Rural"])
            & df["service_type"].isin(ANALYSIS_SERVICE_TYPES)
            & df["nearest_public_transport_km"].notna()
            & df["overall_rating_binary"].notna()
        ].copy()

        scoped["transport_access_quartile"] = pd.qcut(
            scoped["nearest_public_transport_km"],
            q=4,
            labels=list(TRANSPORT_QUARTILE_LABELS),
            duplicates="drop",
        )
        return scoped

    def _build_risk_scope(self):
        risk = self._analysis_df.loc[
            self._analysis_df["service_type"].eq(RISK_SERVICE_TYPE)
            & self._analysis_df["number_of_approved_places"].notna()
        ].copy()

        poor_access_cutoff = float(risk["nearest_public_transport_km"].quantile(TRANSPORT_RISK_QUANTILE))
        low_capacity_cutoff = float(risk["number_of_approved_places"].quantile(CAPACITY_RISK_QUANTILE))

        risk["poor_access_flag"] = risk["nearest_public_transport_km"] >= poor_access_cutoff
        risk["weak_quality_flag"] = risk["overall_rating_binary"].eq("Below Meeting NQS")
        risk["low_capacity_flag"] = risk["number_of_approved_places"] <= low_capacity_cutoff
        risk["gap_score"] = (
            risk["poor_access_flag"].astype(int)
            + risk["weak_quality_flag"].astype(int)
            + risk["low_capacity_flag"].astype(int)
        )
        risk["gap_label"] = risk["gap_score"].astype(int).astype(str) + " gaps"
        return risk, poor_access_cutoff, low_capacity_cutoff

    @property
    def all_services(self) -> pd.DataFrame:
        return self._df.copy()

    @property
    def analysis_services(self) -> pd.DataFrame:
        return self._analysis_df.copy()

    @property
    def risk_services(self) -> pd.DataFrame:
        return self._risk_df.copy()

    @property
    def poor_access_cutoff(self) -> float:
        return self._poor_access_cutoff

    @property
    def low_capacity_cutoff(self) -> float:
        return self._low_capacity_cutoff


@lru_cache(maxsize=1)
def get_repository() -> DataRepository:
    return DataRepository()

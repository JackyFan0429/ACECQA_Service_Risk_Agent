import os
from pathlib import Path

# In local editable installs, the package lives under <repo>/src/acecqa_agent.
# In a Docker/non-editable wheel install, __file__ lives under site-packages,
# so the repository root must be supplied explicitly.
PROJECT_ROOT = Path(
    os.getenv("ACECQA_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
).expanduser().resolve()
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "education_services_cleaned.csv"

ANALYSIS_SERVICE_TYPES = ("Centre-Based Care", "Family Day Care")
RISK_SERVICE_TYPE = "Centre-Based Care"
TRANSPORT_RISK_QUANTILE = 0.75
CAPACITY_RISK_QUANTILE = 0.25

TRANSPORT_QUARTILE_LABELS = (
    "Q1 Closest",
    "Q2",
    "Q3",
    "Q4 Farthest",
)

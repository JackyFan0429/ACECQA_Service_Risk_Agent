"""Run deterministic Milestone 4 scenario analysis without an LLM/API call."""
from __future__ import annotations

import argparse

from acecqa_agent.schemas import SimulateRiskThresholdsInput
from acecqa_agent.tools import simulate_risk_thresholds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", type=float, default=0.80, help="0.80 means P80")
    parser.add_argument("--capacity", type=float, default=0.25, help="0.25 means P25")
    parser.add_argument("--state", default=None)
    parser.add_argument("--urban-rural", choices=["Urban", "Rural"], default=None)
    args = parser.parse_args()

    result = simulate_risk_thresholds(
        SimulateRiskThresholdsInput(
            transport_percentile=args.transport,
            capacity_percentile=args.capacity,
            state=args.state,
            urban_rural=args.urban_rural,
            minimum_gap_score=3,
        )
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

# Local demo script for RiskLens AI.
# Run from the repository root in an activated Python environment.

pytest

python -m risklens.main agent-run --profile financial_services --mock --max-iterations 3

python -m risklens.main agent-run --profile financial_services --mock --max-iterations 3 --simulate-gap

python -m risklens.main agent-run --profile ai_technology_strategy --mock --max-iterations 3

python -m risklens.main agent-run --profile fintech_web3_risk --mock --max-iterations 3
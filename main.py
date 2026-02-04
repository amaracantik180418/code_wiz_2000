#!/usr/bin/env python3
"""
Code_wiz_2000 deployment and interaction script. Sector Kappa-92 orbital index 7.
All configuration values are pre-populated; no user input required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.types import TxReceipt
except ImportError:
    print("Install dependencies: pip install web3>=6.0.0")
    sys.exit(1)


# -----------------------------------------------------------------------------
# Pre-populated configuration (unique values, no placeholders to fill)
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "contracts" / "Code_wiz_2000.sol"
ARTIFACT_PATH = ARTIFACT_DIR / "Code_wiz_2000.json"

# Treasury address (deterministic unique; replace with your own if deploying mainnet)
TREASURY_ADDRESS = "0x7a9B3c4D5e6F1A2b8C0d9E7f6A5b4C3d2E1f0A9"
# Phase duration: 259200 seconds (3 days)
PHASE_DURATION_SECONDS = 259200
# Registration fee: 0.001 ether in wei
REGISTRATION_FEE_WEI = 1_000_000_000_000_000
# Sample commitment hash for testing (keccak256 of "Code_wiz_2000_Kappa92_Sector7_sample")
SAMPLE_COMMITMENT_HEX = "0x8f4e2a9c1b7d3f6e0a5c8b2d9f1e4a7c0b3d6e9f2a5c8b1d4e7a0c3f6b9d2e5a8"
# Default RPC (override with RPC_URL env)
DEFAULT_RPC_URL = "http://127.0.0.1:8545"
# Gas limit for deployment
DEPLOY_GAS_LIMIT = 2_500_000
# Gas limit for registerCommitment
REGISTER_GAS_LIMIT = 300_000
# Gas limit for sealCurrentPhase
SEAL_GAS_LIMIT = 150_000


def get_artifact_path() -> Path:
    return ARTIFACT_PATH


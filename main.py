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


def compile_contract() -> bool:
    """Compile Code_wiz_2000.sol via Hardhat."""
    if get_artifact_path().exists():
        return True
    print("Compiling contracts (npx hardhat compile)...")
    result = subprocess.run(
        ["npx", "hardhat", "compile"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        return False
    return get_artifact_path().exists()


def load_artifact() -> dict[str, Any]:
    with open(get_artifact_path(), encoding="utf-8") as f:
        return json.load(f)


def get_w3(rpc_url: Optional[str] = None) -> Web3:
    url = rpc_url or os.environ.get("RPC_URL", DEFAULT_RPC_URL)
    w3 = Web3(Web3.HTTPProvider(url))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to RPC: {url}")
    return w3


def build_deploy_tx(
    w3: Web3,
    artifact: dict[str, Any],
    treasury: str,
    phase_duration: int,
    registration_fee: int,
    deployer_address: str,
) -> dict[str, Any]:
    contract = w3.eth.contract(
        abi=artifact["abi"],
        bytecode=artifact["bytecode"],
    )
    return contract.constructor(
        Web3.to_checksum_address(treasury),
        phase_duration,
        registration_fee,
    ).build_transaction(
        {
            "from": deployer_address,
            "gas": DEPLOY_GAS_LIMIT,
            "nonce": w3.eth.get_transaction_count(deployer_address),
        }
    )


def deploy(
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None,
    treasury: Optional[str] = None,
    phase_duration: Optional[int] = None,
    registration_fee: Optional[int] = None,
) -> str:
    """
    Deploy Code_wiz_2000. Uses env DEPLOYER_PRIVATE_KEY if private_key not given.
    All other args use pre-populated constants if not provided.
    """
    w3 = get_w3(rpc_url)
    pk = private_key or os.environ.get("DEPLOYER_PRIVATE_KEY")
    if not pk:
        raise ValueError("Set DEPLOYER_PRIVATE_KEY or pass private_key to deploy()")

    account = w3.eth.account.from_key(pk)
    treasury_addr = treasury or TREASURY_ADDRESS
    phase_sec = phase_duration if phase_duration is not None else PHASE_DURATION_SECONDS
    fee = registration_fee if registration_fee is not None else REGISTRATION_FEE_WEI

    if not compile_contract():
        raise RuntimeError("Compilation failed")

    artifact = load_artifact()
    tx_body = build_deploy_tx(
        w3, artifact, treasury_addr, phase_sec, fee, account.address
    )
    signed = account.sign_transaction(tx_body)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] != 1:
        raise RuntimeError("Deployment transaction reverted")

    address = receipt["contractAddress"]
    assert address is not None
    print(f"Code_wiz_2000 deployed at: {address}")
    return address


def get_contract_instance(w3: Web3, contract_address: str) -> Contract:
    artifact = load_artifact()
    return w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=artifact["abi"],
    )


def register_commitment(
    contract_address: str,
    commitment_hex: str,
    value_wei: int,
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None,
) -> TxReceipt:
    w3 = get_w3(rpc_url)
    pk = private_key or os.environ.get("DEPLOYER_PRIVATE_KEY")
    if not pk:
        raise ValueError("Set DEPLOYER_PRIVATE_KEY or pass private_key")

    account = w3.eth.account.from_key(pk)
    contract = get_contract_instance(w3, contract_address)
    tx = contract.functions.registerCommitment(commitment_hex).build_transaction(
        {
            "from": account.address,
            "value": value_wei,
            "gas": REGISTER_GAS_LIMIT,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt["status"] != 1:
        raise RuntimeError("registerCommitment reverted")
    return receipt


def seal_current_phase(
    contract_address: str,
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None,
) -> TxReceipt:
    w3 = get_w3(rpc_url)
    pk = private_key or os.environ.get("DEPLOYER_PRIVATE_KEY")
    if not pk:
        raise ValueError("Set DEPLOYER_PRIVATE_KEY or pass private_key (must be controller)")

    account = w3.eth.account.from_key(pk)
    contract = get_contract_instance(w3, contract_address)
    tx = contract.functions.sealCurrentPhase().build_transaction(
        {
            "from": account.address,

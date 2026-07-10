"""Automated tests for the Bitcoin double-spending laboratory."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "bitcoin"
    / "00-double-spend"
    / "lab"
    / "double_spend_lab.py"
)

MODULE_SPEC = importlib.util.spec_from_file_location(
    "double_spend_lab",
    MODULE_PATH,
)

if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise ImportError(
        f"Unable to load laboratory module from {MODULE_PATH}"
    )

lab = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = lab
MODULE_SPEC.loader.exec_module(lab)


class TransactionValidationTests(unittest.TestCase):
    """Tests for transaction-level validation."""

    def setUp(self) -> None:
        self.genesis = lab.create_demo_state()
        self.transaction_a, self.transaction_b = (
            lab.create_conflicting_transactions()
        )

    def test_valid_transaction_passes_validation(self) -> None:
        lab.validate_transaction(
            self.transaction_a,
            self.genesis.utxos,
        )

    def test_confirmed_double_spend_is_rejected(self) -> None:
        block_a = lab.Block(
            block_id="block-a",
            parent_id="genesis",
            transactions=(self.transaction_a,),
            work=1,
        )

        chain_a = lab.connect_block(
            block_a,
            self.genesis,
        )

        with self.assertRaises(lab.ValidationError):
            lab.validate_transaction(
                self.transaction_b,
                chain_a.utxos,
            )

    def test_duplicate_input_is_rejected(self) -> None:
        transaction = lab.Transaction(
            txid="tx-duplicate",
            inputs=(
                ("funding", 0),
                ("funding", 0),
            ),
            outputs=(
                lab.TxOutput(
                    owner="Bob",
                    amount=99_000_000,
                ),
            ),
        )

        with self.assertRaises(lab.ValidationError):
            lab.validate_transaction(
                transaction,
                self.genesis.utxos,
            )

    def test_transaction_cannot_create_value(self) -> None:
        transaction = lab.Transaction(
            txid="tx-inflation",
            inputs=(("funding", 0),),
            outputs=(
                lab.TxOutput(
                    owner="Mallory",
                    amount=110_000_000,
                ),
            ),
        )

        with self.assertRaises(lab.ValidationError):
            lab.validate_transaction(
                transaction,
                self.genesis.utxos,
            )

    def test_transaction_fee_is_calculated_correctly(self) -> None:
        fee = lab.calculate_transaction_fee(
            self.transaction_a,
            self.genesis.utxos,
        )

        self.assertEqual(fee, 100_000)

    def test_apply_transaction_updates_utxo_set(self) -> None:
        utxos = dict(self.genesis.utxos)

        fee = lab.apply_transaction(
            self.transaction_a,
            utxos,
        )

        self.assertEqual(fee, 100_000)
        self.assertNotIn(("funding", 0), utxos)
        self.assertIn(("tx-a", 0), utxos)
        self.assertEqual(
            utxos[("tx-a", 0)].owner,
            "Bob",
        )


class MempoolTests(unittest.TestCase):
    """Tests for simplified mempool behavior."""

    def setUp(self) -> None:
        self.genesis = lab.create_demo_state()
        self.transaction_a, self.transaction_b = (
            lab.create_conflicting_transactions()
        )

    def test_mempool_accepts_valid_transaction(self) -> None:
        mempool = lab.Mempool()

        mempool.accept(
            self.transaction_a,
            self.genesis.utxos,
        )

        self.assertTrue(
            mempool.contains("tx-a")
        )

        self.assertEqual(
            len(mempool),
            1,
        )

    def test_mempool_rejects_conflicting_spend(self) -> None:
        mempool = lab.Mempool()

        mempool.accept(
            self.transaction_a,
            self.genesis.utxos,
        )

        with self.assertRaises(lab.ValidationError):
            mempool.accept(
                self.transaction_b,
                self.genesis.utxos,
            )

    def test_mempool_rejects_duplicate_transaction_id(self) -> None:
        mempool = lab.Mempool()

        mempool.accept(
            self.transaction_a,
            self.genesis.utxos,
        )

        with self.assertRaises(lab.ValidationError):
            mempool.accept(
                self.transaction_a,
                self.genesis.utxos,
            )

    def test_remove_releases_claimed_outpoint(self) -> None:
        mempool = lab.Mempool()

        mempool.accept(
            self.transaction_a,
            self.genesis.utxos,
        )

        mempool.remove("tx-a")

        self.assertFalse(
            mempool.contains("tx-a")
        )

        mempool.accept(
            self.transaction_b,
            self.genesis.utxos,
        )

        self.assertTrue(
            mempool.contains("tx-b")
        )


class BlockValidationTests(unittest.TestCase):
    """Tests for block connection and block-level validation."""

    def setUp(self) -> None:
        self.genesis = lab.create_demo_state()
        self.transaction_a, self.transaction_b = (
            lab.create_conflicting_transactions()
        )

    def test_valid_block_connects(self) -> None:
        block = lab.Block(
            block_id="block-a",
            parent_id="genesis",
            transactions=(self.transaction_a,),
            work=1,
        )

        state = lab.connect_block(
            block,
            self.genesis,
        )

        self.assertEqual(
            state.tip,
            "block-a",
        )

        self.assertEqual(
            state.chainwork,
            1,
        )

        self.assertIn(
            ("tx-a", 0),
            state.utxos,
        )

    def test_block_cannot_contain_both_conflicts(self) -> None:
        block = lab.Block(
            block_id="bad-block",
            parent_id="genesis",
            transactions=(
                self.transaction_a,
                self.transaction_b,
            ),
            work=1,
        )

        with self.assertRaises(lab.ValidationError):
            lab.connect_block(
                block,
                self.genesis,
            )

    def test_block_parent_must_match_chain_tip(self) -> None:
        block = lab.Block(
            block_id="block-a",
            parent_id="wrong-parent",
            transactions=(self.transaction_a,),
            work=1,
        )

        with self.assertRaises(lab.ValidationError):
            lab.connect_block(
                block,
                self.genesis,
            )

    def test_child_transaction_can_spend_parent_output_in_same_block(
        self,
    ) -> None:
        parent_transaction = lab.Transaction(
            txid="tx-parent",
            inputs=(("funding", 0),),
            outputs=(
                lab.TxOutput(
                    owner="Bob",
                    amount=90_000_000,
                ),
            ),
        )

        child_transaction = lab.Transaction(
            txid="tx-child",
            inputs=(("tx-parent", 0),),
            outputs=(
                lab.TxOutput(
                    owner="Carol",
                    amount=80_000_000,
                ),
            ),
        )

        block = lab.Block(
            block_id="block-parent-child",
            parent_id="genesis",
            transactions=(
                parent_transaction,
                child_transaction,
            ),
            work=1,
        )

        state = lab.connect_block(
            block,
            self.genesis,
        )

        self.assertNotIn(
            ("tx-parent", 0),
            state.utxos,
        )

        self.assertIn(
            ("tx-child", 0),
            state.utxos,
        )


class ChainSelectionTests(unittest.TestCase):
    """Tests for cumulative-work chain selection."""

    def setUp(self) -> None:
        self.genesis = lab.create_demo_state()
        self.transaction_a, self.transaction_b = (
            lab.create_conflicting_transactions()
        )

    def test_greater_chainwork_wins(self) -> None:
        chain_a = lab.connect_block(
            lab.Block(
                block_id="block-a",
                parent_id="genesis",
                transactions=(self.transaction_a,),
                work=1,
            ),
            self.genesis,
        )

        chain_b = lab.connect_block(
            lab.Block(
                block_id="block-b",
                parent_id="genesis",
                transactions=(self.transaction_b,),
                work=3,
            ),
            self.genesis,
        )

        best = lab.select_best_chain(
            (chain_a, chain_b)
        )

        self.assertEqual(
            best.tip,
            "block-b",
        )

        self.assertEqual(
            best.chainwork,
            3,
        )

        self.assertIn(
            ("tx-b", 0),
            best.utxos,
        )

        self.assertNotIn(
            ("tx-a", 0),
            best.utxos,
        )

    def test_empty_candidate_list_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lab.select_best_chain(())


class DataModelTests(unittest.TestCase):
    """Tests for defensive validation in data models."""

    def test_output_amount_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            lab.TxOutput(
                owner="Alice",
                amount=0,
            )

    def test_output_owner_cannot_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            lab.TxOutput(
                owner="",
                amount=1,
            )

    def test_transaction_requires_inputs(self) -> None:
        with self.assertRaises(ValueError):
            lab.Transaction(
                txid="tx-empty-inputs",
                inputs=(),
                outputs=(
                    lab.TxOutput(
                        owner="Alice",
                        amount=1,
                    ),
                ),
            )

    def test_transaction_requires_outputs(self) -> None:
        with self.assertRaises(ValueError):
            lab.Transaction(
                txid="tx-empty-outputs",
                inputs=(("funding", 0),),
                outputs=(),
            )

    def test_block_work_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            lab.Block(
                block_id="invalid-block",
                parent_id="genesis",
                transactions=(),
                work=0,
            )


if __name__ == "__main__":
    unittest.main()

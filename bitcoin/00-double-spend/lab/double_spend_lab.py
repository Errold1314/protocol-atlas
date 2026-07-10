"""Educational Bitcoin double-spending laboratory.

This module demonstrates:

1. UTXO-based transaction validation.
2. Mempool conflict detection.
3. Block-level double-spend rejection.
4. Chain selection based on cumulative work.
5. Simplified chain reorganization behavior.

This project is designed for education only. It is not a complete Bitcoin
implementation and must not be used for real financial transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


SATS_PER_BTC = 100_000_000

OutPoint = Tuple[str, int]
UTXOSet = Dict[OutPoint, "TxOutput"]


class ValidationError(ValueError):
    """Raised when a transaction or block violates a validation rule."""


@dataclass(frozen=True)
class TxOutput:
    """Represents a simplified transaction output."""

    owner: str
    amount: int

    def __post_init__(self) -> None:
        if not self.owner.strip():
            raise ValueError("output owner cannot be empty")

        if self.amount <= 0:
            raise ValueError("output amount must be positive")


@dataclass(frozen=True)
class Transaction:
    """Represents a simplified Bitcoin-like transaction."""

    txid: str
    inputs: Tuple[OutPoint, ...]
    outputs: Tuple[TxOutput, ...]

    def __post_init__(self) -> None:
        if not self.txid.strip():
            raise ValueError("transaction ID cannot be empty")

        if not self.inputs:
            raise ValueError("transaction must contain at least one input")

        if not self.outputs:
            raise ValueError("transaction must contain at least one output")


@dataclass(frozen=True)
class Block:
    """Represents a simplified block."""

    block_id: str
    parent_id: str | None
    transactions: Tuple[Transaction, ...]
    work: int

    def __post_init__(self) -> None:
        if not self.block_id.strip():
            raise ValueError("block ID cannot be empty")

        if self.work <= 0:
            raise ValueError("block work must be positive")


@dataclass
class ChainState:
    """Represents the state produced by one candidate blockchain branch."""

    tip: str | None
    chainwork: int
    utxos: UTXOSet

    def copy(self) -> "ChainState":
        """Return an independent copy of this chain state."""

        return ChainState(
            tip=self.tip,
            chainwork=self.chainwork,
            utxos=dict(self.utxos),
        )


def format_outpoint(outpoint: OutPoint) -> str:
    """Return a human-readable outpoint."""

    txid, index = outpoint
    return f"{txid}:{index}"


def calculate_transaction_fee(
    transaction: Transaction,
    utxos: UTXOSet,
) -> int:
    """Calculate the transaction fee from current UTXO values."""

    input_total = sum(utxos[outpoint].amount for outpoint in transaction.inputs)
    output_total = sum(output.amount for output in transaction.outputs)

    return input_total - output_total


def validate_transaction(
    transaction: Transaction,
    utxos: UTXOSet,
) -> None:
    """Validate a transaction against the supplied UTXO set.

    This simplified validator checks:

    - duplicate inputs;
    - missing or already-spent inputs;
    - positive output values;
    - value conservation.
    """

    if len(set(transaction.inputs)) != len(transaction.inputs):
        raise ValidationError(
            f"{transaction.txid}: duplicate input inside transaction"
        )

    input_total = 0

    for outpoint in transaction.inputs:
        coin = utxos.get(outpoint)

        if coin is None:
            raise ValidationError(
                f"{transaction.txid}: missing or already-spent input "
                f"{format_outpoint(outpoint)}"
            )

        input_total += coin.amount

    output_total = 0

    for output in transaction.outputs:
        if output.amount <= 0:
            raise ValidationError(
                f"{transaction.txid}: output amounts must be positive"
            )

        output_total += output.amount

    if output_total > input_total:
        raise ValidationError(
            f"{transaction.txid}: output value exceeds input value"
        )


def apply_transaction(
    transaction: Transaction,
    utxos: UTXOSet,
) -> int:
    """Apply a valid transaction to a mutable UTXO set.

    Returns:
        The transaction fee in satoshis.
    """

    validate_transaction(transaction, utxos)

    fee = calculate_transaction_fee(transaction, utxos)

    for outpoint in transaction.inputs:
        del utxos[outpoint]

    for output_index, output in enumerate(transaction.outputs):
        new_outpoint = (transaction.txid, output_index)

        if new_outpoint in utxos:
            raise ValidationError(
                f"{transaction.txid}: duplicate transaction output identifier"
            )

        utxos[new_outpoint] = output

    return fee


class Mempool:
    """Simplified mempool with outpoint conflict tracking."""

    def __init__(self) -> None:
        self.transactions: Dict[str, Transaction] = {}
        self.spent_outpoints: Dict[OutPoint, str] = {}

    def __len__(self) -> int:
        return len(self.transactions)

    def contains(self, txid: str) -> bool:
        """Return whether a transaction is currently in the mempool."""

        return txid in self.transactions

    def accept(
        self,
        transaction: Transaction,
        active_utxos: UTXOSet,
    ) -> None:
        """Validate and accept a transaction into the mempool."""

        if transaction.txid in self.transactions:
            raise ValidationError(
                f"{transaction.txid}: transaction already exists in mempool"
            )

        validate_transaction(transaction, active_utxos)

        for outpoint in transaction.inputs:
            conflicting_txid = self.spent_outpoints.get(outpoint)

            if conflicting_txid is not None:
                raise ValidationError(
                    f"{transaction.txid}: mempool conflict with "
                    f"{conflicting_txid} on {format_outpoint(outpoint)}"
                )

        self.transactions[transaction.txid] = transaction

        for outpoint in transaction.inputs:
            self.spent_outpoints[outpoint] = transaction.txid

    def remove(self, txid: str) -> None:
        """Remove a transaction and release its claimed outpoints."""

        transaction = self.transactions.pop(txid, None)

        if transaction is None:
            return

        for outpoint in transaction.inputs:
            current_owner = self.spent_outpoints.get(outpoint)

            if current_owner == txid:
                del self.spent_outpoints[outpoint]

    def remove_confirmed(
        self,
        transactions: Iterable[Transaction],
    ) -> None:
        """Remove transactions that were confirmed in a connected block."""

        for transaction in transactions:
            self.remove(transaction.txid)

    def remove_conflicts(
        self,
        transactions: Iterable[Transaction],
    ) -> None:
        """Remove mempool transactions conflicting with confirmed transactions."""

        confirmed_inputs = {
            outpoint
            for transaction in transactions
            for outpoint in transaction.inputs
        }

        conflicting_txids = {
            txid
            for outpoint, txid in self.spent_outpoints.items()
            if outpoint in confirmed_inputs
        }

        for txid in conflicting_txids:
            self.remove(txid)


def connect_block(
    block: Block,
    parent_state: ChainState,
) -> ChainState:
    """Validate and apply a block to a parent chain state."""

    if block.parent_id != parent_state.tip:
        raise ValidationError(
            f"{block.block_id}: parent {block.parent_id!r} does not match "
            f"current tip {parent_state.tip!r}"
        )

    next_utxos = dict(parent_state.utxos)

    for transaction in block.transactions:
        apply_transaction(transaction, next_utxos)

    return ChainState(
        tip=block.block_id,
        chainwork=parent_state.chainwork + block.work,
        utxos=next_utxos,
    )


def select_best_chain(
    candidate_states: Iterable[ChainState],
) -> ChainState:
    """Select the valid candidate with the greatest cumulative work."""

    states: List[ChainState] = list(candidate_states)

    if not states:
        raise ValueError("at least one candidate chain state is required")

    return max(
        states,
        key=lambda state: (
            state.chainwork,
            state.tip or "",
        ),
    )


def create_demo_state() -> ChainState:
    """Create the initial educational chain state."""

    return ChainState(
        tip="genesis",
        chainwork=0,
        utxos={
            ("funding", 0): TxOutput(
                owner="Alice",
                amount=1 * SATS_PER_BTC,
            )
        },
    )


def create_conflicting_transactions() -> Tuple[Transaction, Transaction]:
    """Create two transactions spending the same outpoint."""

    transaction_a = Transaction(
        txid="tx-a",
        inputs=(("funding", 0),),
        outputs=(
            TxOutput(
                owner="Bob",
                amount=99_900_000,
            ),
        ),
    )

    transaction_b = Transaction(
        txid="tx-b",
        inputs=(("funding", 0),),
        outputs=(
            TxOutput(
                owner="Carol",
                amount=99_900_000,
            ),
        ),
    )

    return transaction_a, transaction_b


def print_utxo_set(utxos: UTXOSet) -> None:
    """Print a readable representation of the UTXO set."""

    for outpoint, output in sorted(utxos.items()):
        print(
            f"   {format_outpoint(outpoint)} "
            f"→ {output.owner} "
            f"→ {output.amount:,} satoshis"
        )


def run_mempool_experiment(
    genesis: ChainState,
    transaction_a: Transaction,
    transaction_b: Transaction,
) -> None:
    """Run the mempool conflict experiment."""

    print("\nExperiment 1: Mempool conflict")
    print("-" * 40)

    mempool = Mempool()

    mempool.accept(transaction_a, genesis.utxos)
    print("1. tx-a accepted into mempool")

    try:
        mempool.accept(transaction_b, genesis.utxos)
    except ValidationError as error:
        print(f"2. tx-b rejected: {error}")


def run_confirmed_double_spend_experiment(
    genesis: ChainState,
    transaction_a: Transaction,
    transaction_b: Transaction,
) -> ChainState:
    """Run the confirmed double-spend experiment."""

    print("\nExperiment 2: Confirmed double-spend rejection")
    print("-" * 40)

    block_a = Block(
        block_id="block-a",
        parent_id="genesis",
        transactions=(transaction_a,),
        work=1,
    )

    chain_a = connect_block(block_a, genesis)

    print("3. block-a accepted")
    print("   Active UTXO set:")
    print_utxo_set(chain_a.utxos)

    try:
        validate_transaction(transaction_b, chain_a.utxos)
    except ValidationError as error:
        print(f"4. tx-b rejected against active UTXO set: {error}")

    return chain_a


def run_intra_block_double_spend_experiment(
    genesis: ChainState,
    transaction_a: Transaction,
    transaction_b: Transaction,
) -> None:
    """Run the same-block double-spend experiment."""

    print("\nExperiment 3: Intra-block double-spend")
    print("-" * 40)

    invalid_block = Block(
        block_id="bad-block",
        parent_id="genesis",
        transactions=(transaction_a, transaction_b),
        work=1,
    )

    try:
        connect_block(invalid_block, genesis)
    except ValidationError as error:
        print(f"5. bad-block rejected: {error}")


def run_chainwork_experiment(
    genesis: ChainState,
    chain_a: ChainState,
    transaction_b: Transaction,
) -> ChainState:
    """Run the competing-chain experiment."""

    print("\nExperiment 4: Competing valid branches")
    print("-" * 40)

    block_b = Block(
        block_id="block-b",
        parent_id="genesis",
        transactions=(transaction_b,),
        work=3,
    )

    chain_b = connect_block(block_b, genesis)

    selected = select_best_chain((chain_a, chain_b))

    print(
        f"6. competing chain selected: {selected.tip} "
        f"(chainwork={selected.chainwork})"
    )

    active_recipient = selected.utxos[("tx-b", 0)].owner
    print(f"7. active recipient: {active_recipient}")

    return selected


def run_value_conservation_experiment(
    genesis: ChainState,
) -> None:
    """Run the value-creation rejection experiment."""

    print("\nExperiment 5: Value conservation")
    print("-" * 40)

    inflationary_transaction = Transaction(
        txid="tx-inflation",
        inputs=(("funding", 0),),
        outputs=(
            TxOutput(
                owner="Mallory",
                amount=110_000_000,
            ),
        ),
    )

    try:
        validate_transaction(
            inflationary_transaction,
            genesis.utxos,
        )
    except ValidationError as error:
        print(f"8. inflationary transaction rejected: {error}")


def run_duplicate_input_experiment(
    genesis: ChainState,
) -> None:
    """Run the duplicate-input experiment."""

    print("\nExperiment 6: Duplicate input")
    print("-" * 40)

    duplicate_input_transaction = Transaction(
        txid="tx-duplicate",
        inputs=(
            ("funding", 0),
            ("funding", 0),
        ),
        outputs=(
            TxOutput(
                owner="Mallory",
                amount=99_000_000,
            ),
        ),
    )

    try:
        validate_transaction(
            duplicate_input_transaction,
            genesis.utxos,
        )
    except ValidationError as error:
        print(f"9. duplicate-input transaction rejected: {error}")


def main() -> None:
    """Run all educational experiments."""

    print("=" * 64)
    print("Protocol Atlas: Bitcoin Double-Spending Laboratory")
    print("=" * 64)

    genesis = create_demo_state()
    transaction_a, transaction_b = create_conflicting_transactions()

    print("\nInitial UTXO set:")
    print_utxo_set(genesis.utxos)

    run_mempool_experiment(
        genesis,
        transaction_a,
        transaction_b,
    )

    chain_a = run_confirmed_double_spend_experiment(
        genesis,
        transaction_a,
        transaction_b,
    )

    run_intra_block_double_spend_experiment(
        genesis,
        transaction_a,
        transaction_b,
    )

    selected_chain = run_chainwork_experiment(
        genesis,
        chain_a,
        transaction_b,
    )

    run_value_conservation_experiment(genesis)
    run_duplicate_input_experiment(genesis)

    print("\nFinal active UTXO set:")
    print_utxo_set(selected_chain.utxos)

    print("\nCore invariant:")
    print(
        "Within one valid chain history, an outpoint may transition "
        "from UNSPENT to SPENT only once."
    )


if __name__ == "__main__":
    main()

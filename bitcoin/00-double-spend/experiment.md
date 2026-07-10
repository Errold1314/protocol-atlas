# Reproducible Double-Spend Experiment

> **Research Goal:** Demonstrate how conflicting transactions interact with the UTXO set, mempool validation, block validation, and chain selection.

## Overview

This experiment models a simplified Bitcoin-like system.

It is not a complete Bitcoin implementation.

The purpose is to make four important properties observable:

1. Two transactions may both be structurally valid while still conflicting.
2. A node should not keep two unconfirmed transactions that spend the same UTXO.
3. A valid block cannot spend the same UTXO twice.
4. A competing valid branch with greater cumulative work becomes the active chain.

The experiment uses a small Python model located at:

[Executable Double-Spend Lab](lab/double_spend_lab.py)

---

# Initial State

Alice owns one unspent transaction output.

| Outpoint    | Owner |         Amount |
| ----------- | ----- | -------------: |
| `funding:0` | Alice | 1.00000000 BTC |

The initial UTXO set is:

```text
funding:0 → Alice → 100,000,000 satoshis
```

---

# Conflicting Transactions

Alice creates two transactions.

## Transaction A

```text
Transaction ID: tx-a
Input: funding:0
Output: Bob receives 99,900,000 satoshis
Fee: 100,000 satoshis
```

## Transaction B

```text
Transaction ID: tx-b
Input: funding:0
Output: Carol receives 99,900,000 satoshis
Fee: 100,000 satoshis
```

Both transactions reference the same input.

```text
funding:0
    │
    ├────────► tx-a → Bob
    │
    └────────► tx-b → Carol
```

The transactions conflict because the same outpoint cannot be consumed twice within one valid chain state.

---

# Experiment 1 — Mempool Conflict

## Goal

Observe how a node handles two unconfirmed transactions that spend the same input.

## Procedure

1. Start with the initial UTXO set.
2. Submit `tx-a` to the mempool.
3. Submit `tx-b` to the same mempool.

## Expected Result

`tx-a` is accepted.

`tx-b` is rejected because `funding:0` is already referenced by `tx-a` inside the mempool.

Expected output:

```text
tx-a accepted into mempool
tx-b rejected: mempool conflict
```

## Interpretation

The active UTXO set still contains `funding:0` because neither transaction has been confirmed.

However, the mempool tracks that `tx-a` already claims the outpoint.

Conceptually:

```text
Active UTXO Set

funding:0 → available
```

```text
Mempool Spend Index

funding:0 → tx-a
```

When `tx-b` arrives, the node detects the conflict through its mempool index.

---

# Experiment 2 — Confirmed Double-Spend Rejection

## Goal

Observe what happens when one conflicting transaction becomes confirmed.

## Procedure

1. Create a block containing `tx-a`.
2. Connect the block to the initial chain state.
3. Validate `tx-b` against the updated UTXO set.

## State Before Block Connection

```text
funding:0 → Alice
```

## State After Connecting `tx-a`

```text
funding:0 → removed
tx-a:0    → Bob
```

## Expected Result

`tx-b` is rejected.

Expected output:

```text
block-a accepted
tx-b rejected against active UTXO set
```

## Interpretation

`tx-b` still references `funding:0`.

That outpoint no longer exists in the active UTXO set.

The transaction therefore fails input validation.

---

# Experiment 3 — Intra-Block Double-Spend

## Goal

Verify that a block cannot contain two transactions that spend the same input.

## Candidate Block

```text
Block bad-block

Transaction 1: tx-a spends funding:0
Transaction 2: tx-b spends funding:0
```

## Validation Process

The block validator processes transactions sequentially.

```text
Initial state:
funding:0 exists
```

Apply `tx-a`:

```text
funding:0 removed
tx-a:0 created
```

Validate `tx-b`:

```text
funding:0 missing
```

## Expected Result

The entire block is rejected.

```text
bad-block rejected: missing or already-spent input
```

## Interpretation

A miner cannot make a double spend valid by placing both transactions inside the same block.

Every full node independently reconstructs the state transition and detects the conflict.

---

# Experiment 4 — Competing Valid Branches

## Goal

Demonstrate how conflicting transactions may exist on separate valid branches.

## Branch A

```text
Genesis
   │
   ▼
Block A
   │
   └── tx-a spends funding:0
```

Chainwork:

```text
1
```

## Branch B

```text
Genesis
   │
   ▼
Block B
   │
   └── tx-b spends funding:0
```

Chainwork:

```text
3
```

Both branches are independently valid.

Each branch spends `funding:0` only once.

## Expected Result

The node selects Branch B because it has greater cumulative work.

Expected output:

```text
competing chain selected: block-b
active recipient: Carol
```

## Interpretation

The transactions do not coexist in one active history.

The node chooses one valid branch as active.

```text
Active branch:

Genesis → Block B → tx-b
```

```text
Inactive branch:

Genesis → Block A → tx-a
```

---

# Experiment 5 — State Reorganization

## Goal

Understand the UTXO changes required during a chain reorganization.

Assume Branch A is active first.

```text
Active state after Block A:

funding:0 removed
tx-a:0 available
```

A stronger Branch B later appears.

The node must conceptually perform two stages.

## Stage 1 — Disconnect Branch A

```text
Remove:
tx-a:0

Restore:
funding:0
```

## Stage 2 — Connect Branch B

```text
Remove:
funding:0

Create:
tx-b:0
```

Final state:

```text
tx-b:0 → Carol
```

## Interpretation

A reorganization is not simply changing a pointer.

The node must reverse the old branch's state transitions and apply the new branch's state transitions.

---

# Experiment 6 — Value Conservation

## Goal

Verify that transactions cannot create value.

Initial input:

```text
100,000,000 satoshis
```

Valid output:

```text
99,900,000 satoshis
```

Fee:

```text
100,000 satoshis
```

Invalid example:

```text
Input total: 100,000,000
Output total: 110,000,000
```

## Expected Result

The invalid transaction is rejected because output value exceeds input value.

## Interpretation

A transaction may destroy value through fees, but it cannot create value outside authorized issuance rules.

---

# Experiment 7 — Duplicate Input Inside One Transaction

## Goal

Distinguish an internal duplicate input from a conflict between two separate transactions.

Invalid transaction:

```text
Transaction tx-invalid

Input 0: funding:0
Input 1: funding:0
```

## Expected Result

The transaction is rejected before normal state transition.

## Interpretation

A single transaction cannot count the same input twice.

This is a structural validation failure.

---

# Running the Experiment

From the repository root:

```bash
python bitcoin/00-double-spend/lab/double_spend_lab.py
```

Expected output:

```text
1. tx-a accepted into mempool
2. tx-b rejected: mempool conflict with tx-a on ('funding', 0)
3. block-a accepted; funding:0 is now spent
4. tx-b rejected against active UTXO set: missing or already-spent input
5. competing chain selected: block-b (chainwork=3)
6. Active recipient: Carol
```

The exact wording may differ slightly if the implementation is updated.

---

# Running the Automated Tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Expected result:

```text
test_block_cannot_contain_both_conflicts ... ok
test_confirmed_double_spend_is_rejected ... ok
test_greater_chainwork_wins ... ok
test_mempool_rejects_conflicting_spend ... ok

Ran 4 tests

OK
```

---

# Test Coverage

The automated tests verify the following properties.

| Test                                       | Property                                                    |
| ------------------------------------------ | ----------------------------------------------------------- |
| `test_mempool_rejects_conflicting_spend`   | One mempool does not accept two spends of the same outpoint |
| `test_confirmed_double_spend_is_rejected`  | A spent input cannot be used again in the active chain      |
| `test_block_cannot_contain_both_conflicts` | One block cannot consume the same UTXO twice                |
| `test_greater_chainwork_wins`              | The valid branch with greater cumulative work is selected   |

---

# Core Invariant

The experiment demonstrates the following state-machine invariant:

```text
Within one valid chain history,
an outpoint may transition from UNSPENT to SPENT only once.
```

Equivalent form:

```text
If an outpoint does not exist in the current UTXO set,
a transaction referencing it cannot be valid.
```

---

# Consensus vs Policy in the Experiment

The experiment intentionally separates two ideas.

## Policy-Like Behavior

The mempool rejects a conflicting transaction because another unconfirmed transaction already claims the same outpoint.

This resembles node policy.

## Consensus-Like Behavior

Block validation rejects a transaction when its input is unavailable in the candidate chain state.

This resembles a consensus rule.

The distinction matters because mempool contents may differ across nodes, while valid block state must be evaluated consistently.

---

# What the Experiment Proves

The experiment proves that:

* valid signatures alone do not solve double-spending;
* transaction validity depends on current state;
* mempool conflicts can be detected before confirmation;
* block validation applies state changes sequentially;
* conflicting spends can exist on separate candidate branches;
* only one conflicting history becomes active;
* cumulative work determines branch selection in the simplified model.

---

# What the Experiment Does Not Prove

The model does not implement:

* Bitcoin Script;
* ECDSA signatures;
* Schnorr signatures;
* transaction serialization;
* transaction IDs derived from serialized data;
* witness data;
* SegWit;
* Taproot;
* Replace-by-Fee;
* package relay;
* fee estimation;
* orphan transactions;
* peer-to-peer propagation;
* real Proof of Work;
* mining difficulty;
* block timestamps;
* coinbase rewards;
* coinbase maturity;
* undo files;
* LevelDB chainstate storage;
* Bitcoin Core concurrency;
* denial-of-service protections;
* complete reorganization logic.

These omissions are intentional.

The model focuses only on the state transitions required to understand double-spending.

---

# Limitations of the Simplified Chainwork Model

The experiment represents work as a positive integer.

Example:

```text
Block A work = 1
Block B work = 3
```

Real Bitcoin Core derives block proof from the encoded difficulty target.

Cumulative chainwork is then calculated from each block's proof.

The simplified integer model demonstrates comparison behavior without implementing compact target encoding or actual hashing.

---

# Suggested Extensions

Future versions may add:

## Replace-by-Fee Simulation

Demonstrate how one mempool transaction can replace another without violating consensus.

## Multi-Input Transactions

Show that a transaction fails if even one input is unavailable.

## Child Transactions

Allow a transaction to spend an output created by an earlier unconfirmed transaction.

## Mempool Dependency Graph

Model parent-child relationships and ancestor limits.

## Reorganization Undo Data

Store explicit undo records rather than constructing independent branch states.

## Real Regtest Integration

Use Bitcoin Core regtest to create conflicting raw transactions and observe actual node behavior.

---

# Optional Bitcoin Core Regtest Experiment

A more realistic future experiment can use Bitcoin Core in regtest mode.

High-level process:

1. Start a regtest node.
2. Generate blocks to create spendable funds.
3. Identify one wallet UTXO.
4. Construct two raw transactions spending the same outpoint.
5. Sign both transactions.
6. Broadcast the first transaction.
7. Attempt to broadcast the conflicting transaction.
8. Mine one transaction into a block.
9. Observe mempool and validation behavior.
10. Create separate nodes or isolated branches to study reorganization.

This process requires careful control of wallet state, node connectivity, and block generation.

It should be documented separately from the simplified Python laboratory.

---

# Expected Learning Outcomes

After completing this experiment, you should be able to explain:

* why two correctly authorized transactions can still conflict;
* how an outpoint identifies a unique spendable output;
* why input existence is a state-dependent condition;
* how a mempool tracks claimed outpoints;
* why a block validator processes transactions sequentially;
* why separate branches may contain conflicting transactions;
* why the active branch determines the current UTXO set;
* why cumulative work resolves competing valid histories.

---

# Related Files

* [Unit Overview](README.md)
* [White Paper Evidence](whitepaper.md)
* [Bitcoin Core Source Code Walkthrough](core-code.md)
* [Executable Double-Spend Lab](lab/double_spend_lab.py)
* [Automated Tests](../../tests/test_double_spend_lab.py)

# Bitcoin Core Source Code Walkthrough

> **Research Goal:** Connect the double-spending model described in the Bitcoin white paper to the transaction-validation, UTXO, mempool, block-connection, and chain-selection logic implemented in Bitcoin Core.

## Scope

This document focuses on the Bitcoin Core components that answer five questions:

1. Where does Bitcoin Core detect an already-spent input?
2. How does the node represent the UTXO set?
3. How are conflicting unconfirmed transactions handled?
4. How does block validation prevent double-spending?
5. How does the node select between competing valid chains?

Bitcoin Core evolves continuously. File locations and function boundaries may change between releases, so source-code study should rely on both file paths and symbol searches.

---

# High-Level Validation Flow

A transaction may reach a Bitcoin Core node through several paths:

* peer-to-peer transaction relay;
* local wallet submission;
* RPC submission;
* block processing;
* chain reorganization.

The validation path depends on whether the transaction is being considered for the mempool or as part of a block.

```text
Incoming Transaction
        │
        ▼
Basic Structural Checks
        │
        ▼
Contextual Validation
        │
        ├──────────────► Mempool Admission
        │
        └──────────────► Block Validation
```

The most important distinction is:

> Mempool acceptance is governed by both consensus rules and node policy, while block acceptance is governed by consensus rules.

---

# Main Source Files

The following files are central to this research unit.

| File                          | Responsibility                                             |
| ----------------------------- | ---------------------------------------------------------- |
| `src/validation.cpp`          | Chain-state validation, block connection, chain activation |
| `src/validation.h`            | Validation interfaces and chain-state declarations         |
| `src/consensus/tx_verify.cpp` | Consensus-level transaction input checks                   |
| `src/consensus/tx_verify.h`   | Transaction verification declarations                      |
| `src/consensus/validation.h`  | Consensus validation state                                 |
| `src/coins.h`                 | UTXO view abstractions                                     |
| `src/coins.cpp`               | UTXO cache and coin-view behavior                          |
| `src/txmempool.h`             | Mempool data structures                                    |
| `src/txmempool.cpp`           | Mempool indexing and conflict tracking                     |
| `src/chain.h`                 | Block-index and chain data structures                      |
| `src/chain.cpp`               | Chain and block-index behavior                             |
| `src/node/transaction.cpp`    | Transaction submission-related node logic                  |
| `src/policy/policy.h`         | Standardness and relay policy                              |
| `src/policy/fees.cpp`         | Fee-related policy logic                                   |

---

# 1. Transaction Representation

Bitcoin transactions are represented primarily by `CTransaction`.

Relevant source areas include:

```text
src/primitives/transaction.h
src/primitives/transaction.cpp
```

A transaction contains:

* version;
* inputs;
* outputs;
* lock time;
* transaction identifier data.

Each input references a previous output using an outpoint.

Conceptually:

```text
COutPoint
├── txid
└── output index
```

A transaction input identifies the exact previous output it wants to consume.

```text
Previous Transaction
        │
        └── Output #0
                │
                ▼
          New Transaction Input
```

Two transactions conflict when they reference the same outpoint.

---

# 2. The UTXO Set

Bitcoin Core does not repeatedly scan the entire blockchain whenever it validates an input.

Instead, it maintains a database of currently spendable outputs.

This database is commonly called the **UTXO set**.

Relevant source files:

```text
src/coins.h
src/coins.cpp
```

Important abstractions include:

* `Coin`
* `CCoinsView`
* `CCoinsViewBacked`
* `CCoinsViewCache`
* `CCoinsViewDB`

---

## `Coin`

A `Coin` represents a spendable transaction output together with metadata.

Conceptually:

```text
Coin
├── transaction output
├── block height
└── coinbase status
```

The output contains:

* value;
* locking script.

The metadata helps enforce rules such as coinbase maturity.

---

## `CCoinsView`

`CCoinsView` defines an interface for reading UTXO information.

Conceptually, it answers questions such as:

```text
Does this outpoint exist?
What output does it contain?
At what height was it created?
Was it created by a coinbase transaction?
```

---

## `CCoinsViewCache`

`CCoinsViewCache` adds an in-memory caching layer above another coin view.

Its purpose is to reduce expensive database operations during validation.

```text
Validation Logic
       │
       ▼
CCoinsViewCache
       │
       ▼
Underlying UTXO Database
```

During block validation, changes can be applied to a temporary cache before being committed.

This is important because Bitcoin Core must validate an entire block before permanently modifying chain state.

---

# 3. Basic Transaction Checks

A transaction first passes checks that do not require access to the current UTXO set.

A commonly relevant symbol is:

```text
CheckTransaction
```

This class of checks typically includes:

* transaction must contain inputs;
* transaction must contain outputs;
* output values must be within valid monetary ranges;
* total output value must not exceed the maximum money supply;
* duplicate inputs inside the same transaction are forbidden;
* transaction size and structure must be valid;
* coinbase structure must follow special rules.

These checks are often called **context-free** or **stateless** checks because they do not yet ask whether the inputs are currently available.

---

## Duplicate Inputs Inside One Transaction

A transaction must not reference the same outpoint twice.

Invalid example:

```text
Transaction X

Input 0 → funding:0
Input 1 → funding:0
```

Even before checking the UTXO set, Bitcoin Core can detect that the transaction contains duplicate inputs.

This is different from two separate transactions conflicting with each other.

---

# 4. Contextual Input Validation

The critical double-spending check happens when Bitcoin Core validates transaction inputs against a coin view.

A key symbol to inspect is:

```text
CheckTxInputs
```

This logic is associated with:

```text
src/consensus/tx_verify.cpp
```

Conceptually, it performs the following process.

```text
For each transaction input:
    locate referenced outpoint
    verify that the coin exists
    verify that it is not already spent
    verify coinbase maturity if applicable
    accumulate input value
```

If a referenced coin does not exist in the current view, the transaction cannot spend it.

The missing coin may mean:

* the referenced transaction never existed;
* the output index is invalid;
* the output has already been spent;
* the required parent transaction is not available in the current validation context.

---

## Core Double-Spend Property

The essential state rule is:

```text
An outpoint must exist in the current coin view
before a transaction is allowed to consume it.
```

After the transaction is applied, that outpoint is removed or marked spent.

Therefore, a later conflicting transaction can no longer find the coin.

```text
Before Tx-A

funding:0 → exists

After Tx-A

funding:0 → unavailable
tx-a:0    → exists
```

When Tx-B later attempts to spend `funding:0`, validation fails.

---

# 5. Script Verification

Input availability alone is not enough.

Bitcoin Core must also verify that the spender satisfies the locking condition attached to the previous output.

This involves Bitcoin Script validation.

Relevant source areas may include:

```text
src/script/interpreter.cpp
src/script/interpreter.h
src/script/script_error.cpp
```

Conceptually:

```text
Previous Output Script
          +
Current Input Witness/Script
          │
          ▼
Script Interpreter
          │
          ▼
Authorized or Rejected
```

This answers:

> Is the spender authorized to consume the available output?

UTXO lookup answers:

> Is the output still available?

Both conditions must be true.

---

# 6. Mempool Admission

The mempool stores valid, unconfirmed transactions that may later be mined.

Relevant files:

```text
src/txmempool.h
src/txmempool.cpp
src/validation.cpp
```

Mempool admission involves more than consensus rules.

A transaction may be consensus-valid but still rejected from a node's mempool because of policy.

Examples include:

* insufficient fee rate;
* non-standard scripts;
* excessive ancestor or descendant limits;
* transaction replacement rules;
* local node configuration.

---

## Mempool Conflict Detection

The mempool tracks which outpoints are already spent by unconfirmed transactions.

Conceptually:

```text
Map of spent outpoints

funding:0 → tx-a
other:2   → tx-c
```

When Tx-B arrives and also references `funding:0`, the node detects a conflict.

```text
Tx-A
Input: funding:0
Status: already in mempool

Tx-B
Input: funding:0
Status: conflict detected
```

Without replacement rules, Tx-B is rejected.

---

# 7. Replace-by-Fee

A mempool conflict is not always permanently rejected.

Bitcoin Core may permit one transaction to replace another under replacement policy.

This is commonly associated with **Replace-by-Fee**.

The exact policy has evolved over time, but the central idea is:

* Tx-B conflicts with Tx-A;
* Tx-B may replace Tx-A if replacement policy requirements are satisfied;
* only one of them remains in the mempool afterward.

This does not violate the no-double-spend rule.

The mempool still maintains only one active candidate spend for the same input.

```text
Before replacement

funding:0 → Tx-A

After replacement

funding:0 → Tx-B
```

Replacement is a policy decision about unconfirmed transactions.

It does not allow both spends to be confirmed in the same valid chain.

---

# 8. Block Validation

When a block arrives, Bitcoin Core does not trust the miner.

The node independently validates the entire block.

Relevant logic is concentrated in:

```text
src/validation.cpp
```

Important symbols may include:

* `CheckBlock`
* `ContextualCheckBlock`
* `ConnectBlock`
* `AcceptBlock`
* `ProcessNewBlock`

The exact call graph may differ across versions.

---

## Conceptual Block-Processing Flow

```text
Received Block
      │
      ▼
Header Checks
      │
      ▼
Proof-of-Work Validation
      │
      ▼
Block Structure Checks
      │
      ▼
Transaction Checks
      │
      ▼
Input and Script Validation
      │
      ▼
Temporary UTXO Updates
      │
      ▼
Commit Valid State
```

---

# 9. `ConnectBlock`

`ConnectBlock` is one of the most important functions for understanding state transitions.

Its role is conceptually to apply a valid block to a previous chain state.

For each transaction, Bitcoin Core:

1. validates transaction inputs;
2. verifies scripts;
3. consumes referenced UTXOs;
4. creates new UTXOs for spendable outputs;
5. records undo information;
6. updates validation-related state.

---

## Sequential Validation Inside a Block

Transactions are processed in block order against an evolving coin view.

Consider this block:

```text
Block

Tx-A spends funding:0
Tx-B spends funding:0
```

The process is:

```text
Initial coin view:
funding:0 exists

Apply Tx-A:
funding:0 removed
tx-a outputs added

Validate Tx-B:
funding:0 no longer exists

Result:
Block rejected
```

This is how Bitcoin Core prevents an intra-block double spend.

---

## Child Transactions in the Same Block

Sequential processing also allows a later transaction to spend an output created earlier in the same block.

```text
Block

Tx-A:
funding:0 → Bob

Tx-B:
tx-a:0 → Carol
```

Processing:

```text
Apply Tx-A
    creates tx-a:0

Validate Tx-B
    finds tx-a:0

Block remains valid
```

Order therefore matters.

---

# 10. UTXO Updates

Applying a transaction changes the coin view.

Conceptually:

```text
For every input:
    spend referenced coin

For every spendable output:
    create new coin
```

Example:

```text
Before

funding:0 → Alice, 1 BTC
```

Transaction:

```text
Input:
funding:0

Outputs:
tx-a:0 → Bob, 0.7 BTC
tx-a:1 → Alice, 0.299 BTC
```

After application:

```text
funding:0 → removed
tx-a:0    → available
tx-a:1    → available
```

The missing amount represents the transaction fee.

---

# 11. Undo Data

Bitcoin Core must be able to reverse a block during a chain reorganization.

When a transaction spends a UTXO, the node records enough information to restore it later.

This is generally referred to as **undo data**.

Conceptually:

```text
Connected Block
      │
      ├── remove spent coins
      ├── add new coins
      └── save restoration data
```

Without undo data, disconnecting a block would require reconstructing old state by rescanning large portions of the blockchain.

---

# 12. `DisconnectBlock`

During a reorganization, Bitcoin Core may remove blocks from the active chain.

A key symbol is:

```text
DisconnectBlock
```

Its conceptual responsibilities are the reverse of `ConnectBlock`.

For each disconnected transaction:

1. remove outputs created by that transaction;
2. restore inputs consumed by that transaction;
3. return the coin view to its previous state.

---

## Example

Active block:

```text
Block A

Tx-A:
funding:0 → Bob
```

State after connection:

```text
funding:0 removed
tx-a:0 available
```

After disconnection:

```text
tx-a:0 removed
funding:0 restored
```

This restoration is essential during chain reorganizations.

---

# 13. Block Index

Bitcoin Core stores metadata for known blocks using `CBlockIndex`.

Relevant source file:

```text
src/chain.h
```

A block-index entry contains information such as:

* block hash;
* previous block pointer;
* height;
* timestamp;
* status flags;
* chainwork;
* transaction count;
* validation state.

The block index allows Bitcoin Core to compare branches without repeatedly reading all block contents.

---

# 14. Chainwork

Bitcoin Core tracks cumulative Proof of Work using a field commonly named:

```text
nChainWork
```

Conceptually:

```text
current block chainwork
=
parent chainwork
+
work represented by current block
```

This allows the node to compare candidate chain tips.

```text
Branch A chainwork: 10,000
Branch B chainwork: 10,500
```

Assuming both branches are valid, Branch B is preferred.

---

# 15. Why Block Count Is Not Enough

Two blocks can represent different amounts of work if mining difficulty differs.

Therefore:

```text
Number of blocks ≠ exact accumulated work
```

Bitcoin Core compares cumulative work rather than visual chain length.

The phrase “longest chain” is historical shorthand.

The implementation follows the valid chain with the greatest accumulated work.

---

# 16. Candidate Chains

Bitcoin Core may know about multiple valid branches simultaneously.

Conceptually:

```text
Known Block Tree

              ┌── A2
Genesis ── A1 ┤
              └── B2 ── B3
```

The node maintains information about candidate tips and determines whether another branch should become active.

Relevant logic is associated with:

```text
ActivateBestChain
ActivateBestChainStep
FindMostWorkChain
```

Exact symbols may vary across releases.

---

# 17. `ActivateBestChain`

`ActivateBestChain` is central to chain selection.

Conceptually, it performs:

```text
Find highest-work valid candidate
            │
            ▼
Compare with current active tip
            │
            ▼
Find common ancestor
            │
            ▼
Disconnect old branch
            │
            ▼
Connect new branch
            │
            ▼
Update active chain
```

---

# 18. Chain Reorganization

A reorganization occurs when a different valid branch accumulates more work than the current active chain.

Example:

```text
Current active chain

Genesis ── A1 ── A2
```

Competing branch:

```text
Genesis ── B1 ── B2 ── B3
```

If the B branch has greater cumulative work, the node reorganizes.

---

## Reorganization Process

```text
Find common ancestor: Genesis

Disconnect:
A2
A1

Connect:
B1
B2
B3
```

During this process, the UTXO set changes from the state produced by Branch A to the state produced by Branch B.

---

# 19. Conflicting Transactions Across Forks

Temporary forks can contain conflicting transactions.

```text
Branch A

Tx-A spends funding:0
```

```text
Branch B

Tx-B spends funding:0
```

Both branches may be independently valid because each branch consumes the output only once within its own history.

The conflict is resolved through chain selection.

```text
Higher-work Branch A
    → Tx-A remains confirmed
    → Tx-B is not part of active history
```

or:

```text
Higher-work Branch B
    → Tx-B remains confirmed
    → Tx-A is removed from active history
```

This illustrates an important principle:

> Double-spending is evaluated relative to a specific candidate chain state.

---

# 20. Transactions After a Reorganization

When blocks are disconnected, some transactions from the removed branch may become unconfirmed again.

Bitcoin Core may reconsider them for mempool admission.

However, a disconnected transaction cannot return to the mempool if it now conflicts with a transaction confirmed on the new active branch.

Example:

```text
Old Branch:
Tx-A spends funding:0

New Branch:
Tx-B spends funding:0
```

After reorganization:

```text
Tx-B is confirmed
funding:0 is spent

Tx-A cannot return as a valid candidate
because its input is unavailable
```

---

# 21. Consensus Rules vs Node Policy

This distinction is essential.

## Consensus Rules

Consensus rules determine whether a block belongs to a valid Bitcoin blockchain.

Examples:

* inputs must exist;
* outputs cannot create unauthorized value;
* scripts must validate;
* coinbase maturity must be respected;
* block Proof of Work must be valid;
* block weight limits must be respected;
* the same UTXO cannot be spent twice in one valid chain state.

Violating a consensus rule makes a block invalid.

---

## Node Policy

Policy determines what an individual node accepts into its mempool and relays.

Examples:

* minimum relay fee;
* standard script forms;
* ancestor and descendant limits;
* replacement behavior;
* dust rules;
* local configuration.

Violating policy may prevent relay without making the transaction invalid under consensus.

---

## Comparison

| Question                                     | Consensus or Policy?      |
| -------------------------------------------- | ------------------------- |
| Does the input exist?                        | Consensus                 |
| Is the signature valid?                      | Consensus                 |
| Does the transaction create excess value?    | Consensus                 |
| Does a block contain a double spend?         | Consensus                 |
| Is the fee rate high enough for this node?   | Policy                    |
| Is the script considered standard?           | Policy                    |
| Can one mempool transaction replace another? | Policy                    |
| Which valid branch has the most work?        | Consensus chain selection |

---

# 22. Miners Do Not Define Validity

Miners create candidate blocks.

They do not have the authority to redefine Bitcoin's consensus rules.

```text
Miner proposes block
        │
        ▼
Full node validates block
        │
        ├── valid → may accept
        └── invalid → reject
```

A miner may include an invalid transaction, but fully validating nodes will reject the entire block.

This is why Bitcoin is not secured by trusting miners.

It is secured by independent validation.

---

# 23. Full Double-Spend Defense Flow

```text
Alice owns funding:0
        │
        ▼
Creates Tx-A and Tx-B
        │
        ▼
Both reference funding:0
        │
        ├──────── Tx-A arrives first
        │             │
        │             ▼
        │       accepted to mempool
        │
        └──────── Tx-B arrives later
                      │
                      ▼
             mempool conflict detected
```

If Tx-A is mined:

```text
ConnectBlock
    │
    ▼
Validate funding:0
    │
    ▼
Remove funding:0
    │
    ▼
Create Tx-A outputs
```

Tx-B now fails against the active UTXO set.

If a competing branch confirms Tx-B and later gains more work:

```text
Disconnect old branch
        │
        ▼
Restore previous UTXOs
        │
        ▼
Connect stronger branch
        │
        ▼
Consume funding:0 through Tx-B
```

Only one spend remains in the active chain.

---

# 24. Simplified Call Graph

The following diagram is conceptual rather than version-specific.

```text
Receive Transaction
        │
        ▼
Transaction Submission Logic
        │
        ▼
Mempool Acceptance
        │
        ├── basic checks
        ├── input lookup
        ├── script checks
        ├── conflict checks
        └── policy checks
```

Block path:

```text
Receive Block
      │
      ▼
ProcessNewBlock
      │
      ▼
AcceptBlock
      │
      ▼
Block Validation
      │
      ▼
ActivateBestChain
      │
      ▼
ConnectBlock / DisconnectBlock
      │
      ▼
Update UTXO State
```

---

# 25. Recommended Source-Code Reading Order

A practical study order is:

## Stage 1 — Transaction Structures

Read:

```text
src/primitives/transaction.h
src/primitives/transaction.cpp
```

Focus on:

* `COutPoint`
* `CTxIn`
* `CTxOut`
* `CTransaction`

---

## Stage 2 — UTXO Representation

Read:

```text
src/coins.h
src/coins.cpp
```

Focus on:

* `Coin`
* `CCoinsView`
* `CCoinsViewCache`

---

## Stage 3 — Consensus Input Checks

Read:

```text
src/consensus/tx_verify.cpp
src/consensus/tx_verify.h
```

Focus on:

* transaction structural checks;
* input existence;
* value accounting;
* coinbase maturity.

---

## Stage 4 — Mempool

Read:

```text
src/txmempool.h
src/txmempool.cpp
```

Focus on:

* outpoint-spend tracking;
* transaction conflicts;
* ancestor relationships;
* replacement logic.

---

## Stage 5 — Block Connection

Read:

```text
src/validation.cpp
```

Search for:

* `ConnectBlock`
* `DisconnectBlock`
* `CheckBlock`
* `ContextualCheckBlock`

---

## Stage 6 — Chain Selection

Read:

```text
src/chain.h
src/chain.cpp
src/validation.cpp
```

Search for:

* `CBlockIndex`
* `nChainWork`
* `ActivateBestChain`
* `FindMostWorkChain`

---

# 26. Source Navigation Commands

After cloning Bitcoin Core:

```bash
git clone https://github.com/bitcoin/bitcoin.git
cd bitcoin
```

Search for important symbols:

```bash
git grep "CheckTransaction"
git grep "CheckTxInputs"
git grep "ConnectBlock"
git grep "DisconnectBlock"
git grep "ActivateBestChain"
git grep "nChainWork"
git grep "CCoinsViewCache"
```

Search for outpoint conflict tracking:

```bash
git grep "mapNextTx"
git grep "GetConflictTx"
git grep "GetConflicts"
```

Some symbols may be renamed or moved in newer releases.

---

# 27. Questions to Ask While Reading

When studying each function, answer:

1. What data does the function receive?
2. Does it enforce consensus or policy?
3. Which coin view does it read?
4. Does it mutate chain state?
5. Can failure invalidate a transaction or an entire block?
6. Is the result cached?
7. What information is required to undo the operation?
8. Does the function assume that earlier checks already succeeded?

This prevents source-code reading from becoming simple line-by-line translation.

---

# 28. Mapping the Educational Lab to Bitcoin Core

| Educational Lab Concept   | Bitcoin Core Equivalent                                  |
| ------------------------- | -------------------------------------------------------- |
| `OutPoint` tuple          | `COutPoint`                                              |
| `TxOutput`                | `CTxOut` and `Coin`                                      |
| UTXO dictionary           | `CCoinsView` / `CCoinsViewCache`                         |
| `validate_transaction`    | `CheckTransaction`, `CheckTxInputs`, script verification |
| `Mempool.spent_outpoints` | Mempool outpoint-spend indexes                           |
| `connect_block`           | `ConnectBlock`                                           |
| reversing state           | `DisconnectBlock` and undo data                          |
| `chainwork` integer       | `CBlockIndex::nChainWork`                                |
| `select_best_chain`       | candidate-chain selection and `ActivateBestChain`        |

The educational model intentionally removes:

* serialization;
* script execution;
* signatures;
* database layers;
* concurrency;
* networking;
* fee policy;
* caching complexity;
* real Proof of Work.

---

# 29. Security Boundaries

Bitcoin Core prevents ledger-level double-spending, but users must still understand confirmation risk.

## Zero Confirmations

A mempool transaction has not yet entered the blockchain.

Different nodes may see different conflicting transactions.

A recipient accepting zero-confirmation payment assumes additional risk.

---

## One Confirmation

The transaction is included in one block, but a short reorganization may still remove it.

---

## Multiple Confirmations

Each additional block increases the amount of work required to replace the transaction's history.

This reduces attack probability but does not create mathematical irreversibility.

---

# 30. Key Conclusions

* Bitcoin Core represents spendable state through the UTXO database.
* A transaction input is valid only if its referenced coin exists in the current coin view.
* Spending a coin removes it from the available state.
* A later conflicting spend fails because the input is no longer available.
* The mempool tracks conflicting unconfirmed spends through outpoint indexes.
* Mempool replacement is policy and does not permit two confirmed spends.
* `ConnectBlock` applies transactions sequentially to a temporary UTXO view.
* `DisconnectBlock` restores previous state using undo information.
* Competing branches may contain conflicting transactions.
* `nChainWork` allows the node to compare valid branches.
* `ActivateBestChain` reorganizes the active state to the highest-work valid chain.
* Miners propose blocks, but full nodes enforce validity.

---

# Related Files

* [Unit Overview](README.md)
* [White Paper Evidence](whitepaper.md)
* [Reproducible Experiment](experiment.md)
* [Executable Double-Spend Lab](lab/double_spend_lab.py)

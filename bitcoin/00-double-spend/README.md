# Without Banks, How Does Bitcoin Prevent Double-Spending?

## The Problem

Digital information can be copied indefinitely.

If Alice creates two different transactions that both attempt to spend the same Bitcoin, how can a decentralized network determine which transaction is valid without relying on a trusted third party?

This is known as the **double-spending problem**, one of the fundamental challenges solved by Bitcoin.

---

# One-Sentence Answer

Bitcoin prevents double-spending by combining:

* the UTXO model,
* transaction validation,
* Proof of Work,
* public block propagation,
* and chain selection based on cumulative work.

Instead of trusting a central authority, every full node independently verifies the same rules and eventually converges on a single valid blockchain.

---

# The Complete Validation Process

## Step 1 — A Transaction References Existing UTXOs

Every Bitcoin transaction consumes one or more existing transaction outputs.

Example:

```text
Funding Transaction

Alice
│
└── Output #0 (1 BTC)
```

A new transaction spends this output.

```text
Input
│
▼
Funding:0
      │
      ▼
Bob
```

Only existing **unspent outputs** may be used as inputs.

---

## Step 2 — Nodes Verify the Transaction

Every full node independently checks whether

* the referenced UTXO exists;
* the UTXO has not already been spent;
* signatures are valid;
* values are conserved;
* transaction format follows consensus rules.

If any check fails, the transaction is rejected immediately.

---

## Step 3 — The Mempool Prevents Obvious Conflicts

Suppose Alice creates two transactions.

```text
Funding:0
      │
      ├────────► Tx-A → Bob
      │
      └────────► Tx-B → Carol
```

Both transactions attempt to spend exactly the same UTXO.

A node may receive Tx-A first.

When Tx-B arrives later, the node detects that the same input is already reserved by another transaction inside its mempool.

Tx-B is therefore rejected (unless specific replacement policies apply).

---

## Step 4 — Miners Build Candidate Blocks

Miners select valid transactions from the mempool.

A candidate block may look like this.

```text
Block

Tx1
Tx2
Tx3
TxA
Tx4
Tx5
```

If a block contains conflicting transactions that spend the same input, every full node will reject that block.

Consensus rules never allow the same UTXO to be consumed twice inside one valid chain.

---

## Step 5 — Proof of Work Produces a Public Ordering

Different miners may discover blocks at nearly the same time.

For a short period, two valid branches may coexist.

```text
Genesis
   │
   ├──────── Block A
   │
   └──────── Block B
```

This situation is temporary.

Nodes continue validating blocks on whichever branch they currently know.

---

## Step 6 — Nodes Select the Chain with the Greatest Cumulative Work

Eventually one branch becomes stronger.

```text
Genesis
   │
   ├──────── Block A
   │
   │
   └──────── Block B
               │
               ▼
            Block C
```

Now the second branch contains more accumulated Proof of Work.

Nodes reorganize to the stronger branch.

The commonly used phrase **"longest chain"** actually means:

> the valid chain with the greatest cumulative Proof of Work.

The number of blocks alone is not the security metric.

---

# Why Digital Signatures Are Not Enough

Digital signatures answer only one question:

> "Did the owner authorize this transaction?"

They do **not** answer another critical question:

> "Has this output already been spent elsewhere?"

Bitcoin solves the second problem using:

* UTXO validation,
* distributed consensus,
* Proof of Work,
* and chain selection.

---

# Responsibilities of Different Components

| Component         | Responsibility                          |
| ----------------- | --------------------------------------- |
| Digital Signature | Proves ownership                        |
| UTXO Set          | Records spendable outputs               |
| Full Node         | Validates transactions and blocks       |
| Mempool           | Stores candidate transactions           |
| Miner             | Packages valid transactions into blocks |
| Proof of Work     | Produces an objective ordering          |
| Chain Selection   | Chooses the strongest valid blockchain  |

---

# Common Misconceptions

## "Signatures prevent double-spending."

Incorrect.

Signatures only prove authorization.

Consensus determines whether the referenced output remains spendable.

---

## "The longest chain always wins."

Partially correct.

Bitcoin follows the **valid chain with the greatest cumulative work**, not simply the chain containing the largest number of blocks.

---

## "A confirmed transaction is impossible to reverse."

Incorrect.

Bitcoin provides **probabilistic security**, not mathematical finality.

Each additional confirmation increases the amount of work required to rewrite history.

---

# Learning Objectives

After completing this unit, you should understand:

* why digital signatures alone cannot solve double-spending;
* how the UTXO model represents ownership;
* how full nodes validate transactions;
* why conflicting transactions cannot both become valid;
* how temporary forks occur;
* why cumulative work determines the active chain;
* why confirmations increase economic security.

---

# Files in This Unit

* **whitepaper.md** — Evidence from the Bitcoin White Paper
* **core-code.md** — Bitcoin Core source-code navigation
* **experiment.md** — Reproducible experiment guide
* **lab/double_spend_lab.py** — Executable educational model

---

# Next Research Questions

* Where exactly does Bitcoin Core reject spent inputs?
* How is the UTXO set updated during block connection?
* How are chain reorganizations implemented?
* How does Replace-by-Fee interact with mempool conflicts?
* How is chainwork calculated inside Bitcoin Core?

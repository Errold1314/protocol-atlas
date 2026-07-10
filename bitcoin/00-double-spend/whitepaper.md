# Evidence from the Bitcoin White Paper

> **Research Goal:** Explain how Bitcoin prevents double-spending using evidence from the original white paper and connect those ideas to modern Bitcoin Core concepts.

**Primary Reference**

> Satoshi Nakamoto. *Bitcoin: A Peer-to-Peer Electronic Cash System* (2008)
> https://bitcoin.org/bitcoin.pdf

---

# Overview

The double-spending problem is one of the fundamental challenges in digital money.

Unlike physical cash, digital information can be copied perfectly. If no trusted authority exists, the network must determine which transaction represents the legitimate transfer of ownership.

Bitcoin solves this problem without relying on banks or centralized payment processors.

Instead, it combines:

* cryptographic signatures,
* public transaction history,
* distributed validation,
* Proof of Work,
* and chain selection based on cumulative work.

These mechanisms together allow independent nodes to converge on a single shared history.

---

# White Paper Sections Relevant to Double-Spending

This document primarily refers to the following sections of the Bitcoin white paper.

| Section    | Topic            | Relevance                                            |
| ---------- | ---------------- | ---------------------------------------------------- |
| Section 2  | Transactions     | Ownership transfer and digital signatures            |
| Section 3  | Timestamp Server | Public ordering of transactions                      |
| Section 4  | Proof of Work    | Preventing inexpensive history modification          |
| Section 5  | Network          | Validation, broadcasting, forks, and chain selection |
| Section 11 | Calculations     | Probability of a successful attack                   |

---

# Section 2 — Transactions

## What the White Paper Says

Bitcoin represents ownership as a chain of digitally signed transactions.

Each transaction spends one or more outputs created by previous transactions.

Instead of transferring balances between accounts, Bitcoin transfers the right to spend existing outputs.

---

## Why Digital Signatures Alone Are Not Enough

Digital signatures answer one important question:

> **Did the owner authorize this transaction?**

They do **not** answer another equally important question:

> **Has this output already been spent somewhere else?**

Consider the following situation.

```text
Funding Transaction

Alice owns:

Funding:0
   │
   ▼
1 BTC
```

Alice creates two different transactions.

```text
Funding:0
    │
    ├────────► Tx-A → Bob
    │
    └────────► Tx-B → Carol
```

Both transactions contain:

* valid signatures;
* correctly formatted data;
* identical inputs.

If signatures alone determined validity, both transactions would appear acceptable.

The network therefore requires additional rules.

---

## The Missing Information

A signature proves authorization.

It does **not** prove uniqueness.

Nodes must know whether the referenced output is currently unspent.

This is why Bitcoin maintains a shared transaction history.

Only one transaction may consume a particular output within a valid chain.

---

# The UTXO Model

Although the white paper does not explicitly use the modern term **UTXO**, the concept naturally follows from its transaction model.

A transaction output has two possible states.

```text
UNSPENT
    │
    ▼
Referenced by a valid transaction
    │
    ▼
SPENT
```

Once spent, that output can never become spendable again within the same blockchain history.

This simple state transition forms the foundation of Bitcoin's ownership model.

---

# Section 3 — Timestamp Server

## Why Ordering Matters

If conflicting transactions exist, the network must determine which one happened first.

Bitcoin accomplishes this without a central clock.

Instead, blocks create a public chronological ordering of accepted transactions.

```text
Transaction
      │
      ▼
Candidate Block
      │
      ▼
Proof of Work
      │
      ▼
Accepted History
```

The timestamp server does not merely record time.

It records **ordering**.

Ordering is what allows every node to agree which transaction consumed an output first.

---

# Section 4 — Proof of Work

## Why History Cannot Be Modified Cheaply

Every block contains the hash of the previous block.

```text
Block A
   │
hash
   ▼
Block B
   │
hash
   ▼
Block C
```

Changing any transaction inside Block A changes its hash.

That immediately invalidates Block B.

Which also invalidates Block C.

An attacker must therefore rebuild every descendant block.

---

## Why Proof of Work Matters

Proof of Work transforms history modification from a simple editing task into a computational race.

Creating a valid block requires repeated hashing until the block satisfies the network difficulty target.

Verification is inexpensive.

Creation is intentionally expensive.

This asymmetry allows nodes to verify blocks quickly while making history modification economically costly.

---

# Section 5 — Network

## Transaction Broadcast

When a user creates a transaction, it is broadcast across the peer-to-peer network.

Each node independently verifies:

* transaction structure;
* signatures;
* referenced outputs;
* consensus rules.

Only valid transactions continue propagating.

---

## Independent Validation

Every node performs the same validation process.

No central server decides whether a transaction is valid.

Consensus emerges because every participant follows identical rules.

```text
Transaction
      │
      ▼
Node A validates
Node B validates
Node C validates
Node D validates
      │
      ▼
Same validation rules
      │
      ▼
Same result
```

---

## Temporary Forks

Sometimes two miners discover blocks almost simultaneously.

```text
Genesis
    │
    ├──────── Block A
    │
    └──────── Block B
```

Both blocks may be valid.

Different nodes may temporarily follow different branches.

This situation is expected.

It is not a failure of consensus.

---

# Chain Selection

Eventually one branch gains another valid block.

```text
Genesis
    │
    ├──────── Block A
    │
    └──────── Block B
                 │
                 ▼
              Block C
```

Now the second branch has accumulated more Proof of Work.

Nodes reorganize to that branch.

The white paper commonly refers to this as following the **longest chain**.

Modern Bitcoin Core terminology is more precise.

Nodes select:

> **the valid chain with the greatest cumulative Proof of Work (chainwork).**

Block count alone is not the deciding factor.

---

# Why Chainwork Is More Accurate Than "Longest Chain"

Suppose two branches exist.

```text
Chain A

100
101
102
103
```

```text
Chain B

100
101
102
```

If Chain B somehow contains more accumulated work because of different difficulty adjustments, it represents the stronger chain.

Security depends on cumulative work, not visual length.

For this reason, modern Bitcoin documentation generally discusses **chainwork** instead of simply counting blocks.

---

# Section 11 — Probability of an Attack

The white paper analyzes an attacker attempting to rewrite confirmed history.

The attacker's probability of success decreases as confirmation depth increases.

More confirmations mean:

* more Proof of Work;
* more accumulated chainwork;
* greater computational cost;
* lower probability of catching up.

Bitcoin therefore provides **probabilistic finality**, not absolute finality.

---

# Putting Everything Together

The complete process can be summarized as follows.

```text
User Creates Transaction
            │
            ▼
Digital Signature
            │
            ▼
Broadcast to Network
            │
            ▼
Independent Node Validation
            │
            ▼
UTXO Verification
            │
            ▼
Accepted into Mempool
            │
            ▼
Included in Candidate Block
            │
            ▼
Proof of Work
            │
            ▼
Block Validation
            │
            ▼
Chain Selection
            │
            ▼
Confirmed Transaction
```

Each stage contributes a different security property.

---

# Responsibilities of Each Mechanism

| Mechanism          | Responsibility                              |
| ------------------ | ------------------------------------------- |
| Digital Signature  | Proves authorization                        |
| Transaction Format | Defines valid state transitions             |
| UTXO Set           | Determines whether outputs remain spendable |
| Full Nodes         | Validate transactions and blocks            |
| Mempool            | Stores candidate transactions               |
| Miners             | Produce candidate blocks                    |
| Proof of Work      | Establishes objective ordering              |
| Chain Selection    | Determines the active blockchain            |

---

# Common Misconceptions

## "Bitcoin prevents double-spending with signatures."

Incorrect.

Signatures prove ownership.

They do not determine whether an output has already been consumed.

---

## "The longest chain wins."

Incomplete.

Bitcoin follows the **valid chain with the greatest cumulative Proof of Work**.

---

## "Blocks make transactions irreversible."

Incorrect.

Blocks increase the cost of rewriting history.

Finality is economic and probabilistic.

---

## "Miners decide what is valid."

Incorrect.

Miners propose blocks.

Full nodes determine whether those blocks satisfy consensus rules.

---

# Key Takeaways

* Digital signatures prove authorization, not uniqueness.
* The UTXO model prevents an output from being spent twice within one valid history.
* Public ordering is required to resolve conflicting transactions.
* Proof of Work makes rewriting history computationally expensive.
* Independent validation removes the need for a trusted authority.
* Chainwork determines the active blockchain.
* Confirmation depth increases economic security against history reorganization.

---

# Suggested Follow-up Reading

* [Mapping these concepts to Bitcoin Core.](core-code.md)
* [Reproducing double-spending behavior in a simplified laboratory.](experiment.md)
* [Executable educational implementation.](experiment.md)

---

# References

1. Satoshi Nakamoto. *Bitcoin: A Peer-to-Peer Electronic Cash System* (2008).
   https://bitcoin.org/bitcoin.pdf

2. Bitcoin Core Documentation
   https://github.com/bitcoin/bitcoin

3. Bitcoin Developer Reference
   https://developer.bitcoin.org/

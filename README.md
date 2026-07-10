# Protocol Atlas

> Understanding the open web through protocols, source code, and reproducible experiments.

Protocol Atlas is not a cryptocurrency encyclopedia and does not provide investment advice.

It explores a more fundamental question:

**How does the open web maintain state, reach consensus, and defend against malicious behavior without a centralized trusted authority?**

## Methodology

Each topic follows the same chain of evidence:

> Problem → Protocol Rules → Source Code Implementation → Reproducible Experiments → Attack Boundaries → Cross-Protocol Comparisons

## Current Research Tracks

* [ ] Bitcoin: Double-spending fundamentals
* [ ] Bitcoin: UTXO validation experiment
* [ ] Bitcoin: Mempool conflict simulation
* [ ] Bitcoin: Chainwork-based chain selection
* [ ] Bitcoin: Full Bitcoin Core transaction validation walkthrough
* [ ] Bitcoin: Blocks and Proof of Work
* [ ] Bitcoin: Peer-to-peer networking
* [ ] Bitcoin: Mining incentives
* [ ] Ethereum: Account model
* [ ] Ethereum: EVM and gas
* [ ] Ethereum: Proof of Stake and finality
* [ ] Cross-protocol comparisons

## First Completed Unit

[Without banks, how does Bitcoin prevent the same unit of digital value from being double-spent?](bitcoin/00-double-spend/README.md)

This unit includes:

* evidence from the Bitcoin white paper;
* a Bitcoin Core source-code navigation map;
* an executable Python UTXO model;
* a mempool conflict simulation;
* a chainwork-based fork-selection experiment;
* automated unit tests;
* a reproducible experiment guide.

## Project Structure

```text
protocol-atlas/
├── README.md
├── LICENSE-CODE
├── bitcoin/
│   └── 00-double-spend/
│       ├── README.md
│       ├── whitepaper.md
│       ├── core-code.md
│       ├── experiment.md
│       └── lab/
│           └── double_spend_lab.py
└── tests/
    └── test_double_spend_lab.py
```

## Run the Experiment

```bash
python bitcoin/00-double-spend/lab/double_spend_lab.py
```

## Run the Tests

```bash
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 4 tests

OK
```

## What the Experiment Demonstrates

The experiment demonstrates four important properties:

1. Two transactions may both be correctly signed but still conflict.
2. A node should not accept two mempool transactions that spend the same UTXO.
3. A valid block cannot spend the same UTXO more than once.
4. When valid competing chains exist, nodes select the chain with the greatest cumulative work.

## Important Distinctions

### Digital Signatures

Digital signatures prove that the owner of a private key authorized a transaction.

They do not prove that the same output was not used in another transaction.

### UTXO Validation

UTXO validation determines whether a referenced output still exists and remains unspent.

### Mempool Policy

Mempool policy determines which unconfirmed transactions a node stores and relays.

Different nodes may use different policies.

### Consensus Rules

Consensus rules determine whether a transaction or block is valid.

A block that spends an unavailable input is invalid.

### Chain Selection

Chain selection determines which valid blockchain history becomes active.

Bitcoin selects the valid chain with the greatest cumulative proof of work.

## Principles

* Prioritize original specifications, white papers, and client source code.
* Clearly distinguish consensus rules, node policy, miner strategy, and personal interpretation.
* Make every major conclusion reproducible.
* Explain both normal behavior and attack boundaries.
* Do not upload private keys, seed phrases, API keys, or real financial information.
* Do not treat educational experiments as production implementations.

## Scope

The current executable lab is an educational model.

It does not implement:

* Bitcoin Script;
* transaction serialization;
* ECDSA or Schnorr signatures;
* real mining;
* network propagation;
* Replace-by-Fee;
* difficulty adjustment;
* complete Bitcoin Core reorganization behavior.

These topics will be added in future research units.

## License

Documentation is licensed under the Creative Commons Attribution 4.0 International License.

Experimental code is licensed under the MIT License.

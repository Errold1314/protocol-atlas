# Without Banks, How Does Bitcoin Prevent Double-Spending?

## The Problem

Digital files can be copied infinitely. If Alice simultaneously transfers control of the same BTC to both Bob and Carol,
how does the network determine which transaction is valid without relying on banks?

## One-Sentence Answer

Bitcoin does not rely on “hidden transactions,” but rather on public broadcasting, node verification, proof-of-work, and the valid chain with the most accumulated work,
allowing the entire network to gradually converge on a single transaction history.

## Key Steps

1. A transaction spends an existing UTXO.
2. Nodes verify whether the UTXO exists, whether the signature is valid, and whether it has already been spent.
3. Miners pack valid transactions into blocks and compete for the right to record them via Proof of Work (PoW).
4. Nodes select the valid chain with the highest cumulative work.
5. Additional subsequent blocks increase the cost of rewriting history.

## Files for This Unit

- [White Paper Evidence](whitepaper.md)
- [Implementation and Terminology](core-code.md)
- [Experiment Log](experiment.md)

## Open Questions

- Why should “longest chain” be understood as “the valid chain with the most cumulative work”?
- Why can a 0-confirmation transaction be double-spent?
- What are the respective responsibilities of nodes (verification) and miners (packaging)?

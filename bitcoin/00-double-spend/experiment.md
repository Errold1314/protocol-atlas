# Experiment: Two Transactions Competing to Spend the Same UTXO

## Assumptions

Alice has one UTXO:

| outpoint | Amount | Owner |
|---|---:|---|
| `tx0:0` | 1 BTC | Alice |

Alice creates two conflicting transactions:

| Transaction | Inputs | Outputs |
|---|---|---|
| Tx-A | `tx0:0` | Bob: 0.999 BTC |
| Tx-B | `tx0:0` | Carol: 0.999 BTC |

## Observation

Both transactions may have valid signatures, but they cannot be included in the same valid ledger at the same time,
because they both reference the same input `tx0:0`.

If Tx-A has been incorporated into a chain accepted by nodes, `tx0:0` in the UTXO set becomes spent.
After that, the input for Tx-B is no longer available and should therefore be rejected.

## Conclusion

Signatures prove “who has the right to spend”;
the UTXO state and chain selection determine “whether this value has already been spent.”

## Next Steps

Use Bitcoin Core’s regtest to create two conflicting transactions and observe the node logs and chain reorganization.

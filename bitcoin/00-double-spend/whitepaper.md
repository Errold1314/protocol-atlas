# Evidence from the White Paper

- Section 2, “Transactions”: Why Digital Signatures Are Not Enough to Prevent Double-Spending
- Section 4, “Proof-of-Work”: Why Modifying the History Requires Re-doing the Work
- Section 5, “Network”: Transaction Broadcast, Block Validation, Forks, and Chain Selection

Original text: [Bitcoin: A Peer-to-Peer Electronic Cash System](https://bitcoin.org/bitcoin.pdf)

## My Understanding

Double-spending is not “someone copying coins,” but rather multiple conflicting transactions attempting to spend the same existing output.
The challenge with Bitcoin is getting distributed nodes to agree on which transaction should be included in the valid history.

## White Paper Evidence: How Bitcoin Prevents Double-Spending

Original Text: [Bitcoin: A Peer-to-Peer Electronic Cash System](https://bitcoin.org/bitcoin.pdf)

This article corresponds to Section 2 (Transactions), Section 4 (Proof-of-Work), and Section 5 (Network) of the white paper.

## 1. Why Can’t Digital Signatures Alone Solve the Double-Spending Problem?

Digital signatures address the issue of **authorization**: they prove that a private-key holder consents to transferring a certain amount of value to a new public key.

However, signatures cannot answer another question: Has the same owner already signed away this value to someone else? Alice could sign two valid transactions using the same input; both signatures might be correct in themselves.

Therefore, Bitcoin also requires the network to establish a single, public history of transaction order. The key idea in Section 2 of the white paper is that, to confirm there are no earlier conflicting transactions, participants must be able to understand the transaction history and reach consensus on which transaction was accepted first.

## 2. Why Does PoW Make Tampering with the History Expensive?

A block records the hash of the previous block within itself. If an attacker modifies a transaction in an earlier block, the block’s hash will change, rendering the hash of the previous block stored in subsequent blocks invalid.

Proof of Work requires miners to continuously try different nonces until the block’s hash meets the current difficulty target. Verifying a valid block is inexpensive, but creating one requires a large number of random attempts.

Therefore, if an attacker wants to rewrite a transaction that has already been confirmed, they must not only re-mine the modified block but also re-mine all subsequent blocks and catch up to the ever-increasing workload of the honest network. The more confirmations a transaction has, the lower the probability of successfully catching up.

## 3. How do nodes choose the same chain during a fork?

When two miners find blocks almost simultaneously, the network may temporarily fork. Some nodes receive Block A first, while others receive Block B first; they can temporarily continue working on the branch they see.

The rule in the white paper is: nodes accept the **valid chain with the most cumulative work** and continue mining at the end of that chain. The commonly referred to “longest chain” does not simply mean the one with more blocks, but the one with more cumulative Proof-of-Work (PoW) invested.

When one branch gains a new valid block and takes the lead, nodes on the other branch will switch to the chain with the higher cumulative work. Blocks that have not been incorporated into the final main chain are called stale blocks; if the transactions within them have not yet been confirmed by the main chain, they may be returned to the pool of candidate transactions to await packaging.

## A Complete Anti-Double-Spend Chain

1. Alice uses her private key to sign and construct a transaction that spends an existing UTXO.
2. The transaction is broadcast to nodes; nodes verify the signature, inputs, and other consensus rules.
3. Miners package valid transactions into candidate blocks and calculate a PoW that meets the difficulty requirement for the block.
4. Successful blocks are broadcast; nodes only accept blocks where the transaction is valid, the inputs have not been spent, and the PoW is correct.
5. If a temporary fork exists, nodes select the valid chain with the highest cumulative work.
6. Subsequent blocks continue to be added, making it increasingly costly to rewrite this history.

## Differences from Common Misconceptions

- **“Signatures prevent double-spending” is inaccurate.** Signatures only prove the right to spend; network consensus determines which of the conflicting spends becomes the valid history.
- **“Longest chain” should not be understood solely as the chain with the most blocks.** The correct focus is on the valid chain with the most cumulative work.
- **“Confirmation” is not mathematically irreversible.** It is an economic security guarantee that strengthens as subsequent work increases.

## Next Steps for Verification

In the Bitcoin Core regtest environment, create two conflicting transactions that spend the same input. Observe that nodes accept only one of them into the valid chain, and observe chain selection after manually creating a fork.

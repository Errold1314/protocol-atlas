# Security Policy

## Educational Scope

Protocol Atlas contains educational protocol research and simplified experimental code.

The repository is not production software.

Do not use its experimental implementations for:

* real cryptocurrency transactions;
* custody of funds;
* wallet generation;
* private-key management;
* transaction signing;
* consensus participation;
* production blockchain infrastructure.

## Sensitive Information

Never submit:

* private keys;
* mnemonic phrases;
* wallet backup files;
* exchange credentials;
* API secrets;
* authentication tokens;
* personally identifiable financial information;
* real payment details.

If sensitive information is committed accidentally, assume it has been compromised and revoke or rotate it immediately.

Deleting the file from the latest commit is not sufficient because it may remain in Git history.

## Reporting a Security Issue

For issues affecting only the educational code, open a GitHub issue with:

* the affected file;
* a clear explanation;
* steps to reproduce;
* expected behavior;
* actual behavior;
* proposed mitigation, if known.

Do not publish active credentials or sensitive data in an issue.

## Upstream Vulnerabilities

If you discover a vulnerability in Bitcoin Core, Ethereum clients, wallet software, or another upstream project, follow that project's responsible-disclosure process.

Do not use Protocol Atlas as the first public disclosure location for an unpatched vulnerability in a live protocol implementation.

## Threat Model

The current Python laboratory does not provide:

* cryptographic authentication;
* network isolation;
* persistent state protection;
* denial-of-service resistance;
* Byzantine fault tolerance;
* secure randomness;
* production-grade input handling.

It should be treated only as an executable teaching model.

## Supported Versions

Protocol Atlas does not currently maintain production release versions.

The latest commit on the default branch is the only actively maintained version.

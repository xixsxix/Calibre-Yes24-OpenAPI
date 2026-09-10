# Security Policy

## Supported version

The current supported release line is **0.4.x**. Security fixes should target the newest published patch release.

## API keys

This plugin requires a YES24 Open API key.

- Enter the key through Calibre's plugin customization UI.
- Do not hard-code the key in `yes24.py`.
- Do not commit `.env`, `.ENV`, screenshots containing keys, or verbose logs that expose credentials.
- Development helpers may read `YES24_API_KEY` from the environment or a local `.ENV` file; those files are ignored by Git.

The plugin sends the key only in the `X-Api-Key` header to the official YES24 Open API endpoint.

## Bug reports

For ordinary metadata bugs, open a GitHub Issue and include only the minimum information needed to reproduce the problem:

```text
Calibre version
plugin version
book title
author
current ISBN, if any
expected result
actual result
relevant YES24 verbose log lines
```

Before posting logs, remove API keys, unrelated local paths, account information, and personal library data.

## Sensitive security reports

Do not post a live API key or another credential in a public Issue. If a report necessarily contains a secret, revoke/rotate that secret first and redact it from any public material.

## Data handling

This repository does not publish captured YES24 API response fixtures. The YES24 Developers FAQ states that YES24 Open API data is YES24 intellectual property and prohibits unauthorized collection, redistribution, and resale. Development fixtures, when used locally, should remain private unless redistribution rights are explicitly confirmed.

## Scope

Issues that may warrant security treatment include:

- accidental disclosure or logging of API credentials
- sending credentials to a non-YES24 endpoint
- unsafe handling of untrusted HTML or API payloads
- arbitrary local file access or modification

Incorrect book matching is primarily a data-quality/safety issue rather than a credential-security issue, but high-impact automatic metadata replacement bugs are still treated as release blockers.
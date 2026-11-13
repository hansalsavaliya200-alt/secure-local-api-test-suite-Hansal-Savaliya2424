# Scope and authorized use

## Scope

- **In scope:** this repository's API running on `127.0.0.1`, and the local training targets listed below when used as described.
- **Out of scope:** all other systems, networks, websites, and people. No system is scanned or tested unless it is owned by me or I have explicit authorization.

## Training resources

- **PortSwigger Web Security Academy:** labs are completed only in PortSwigger's own lab environment. Completed labs are recorded in `portswigger-lab-log.md`.
- **OWASP Juice Shop:** optional training target. If used, it must run locally and must not be exposed to a network.

## Test data provenance

All application data is synthetic: four demo accounts (`alice`, `bob`, `carol`, `dave`), their `<name>-demo-Passw0rd!` passwords, and example tickets. They do not represent real people or credentials. Signing keys are generated at start-up or provided through an environment variable; no real key is committed. `.env.example` contains only a placeholder.

## Safety rules followed

- No real credentials, API keys, or personal data are used in the repository, report, or video.
- Mutation tests run against temporary project copies; the working source is left unchanged.
- Security issues are described and tested defensively. The project does not include exploit code.

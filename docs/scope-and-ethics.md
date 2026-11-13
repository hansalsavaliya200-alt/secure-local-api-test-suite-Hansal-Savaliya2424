# Scope and ethics statement

## Scope

- **In scope:** the API in this repository, running on `127.0.0.1` on my own computer, and the intentionally vulnerable local training targets named below.
- **Out of scope:** every other system, network, website or person. No scanning, probing or testing of anything I do not own or have not been explicitly authorised to test.

## Training resources

- **PortSwigger Web Security Academy:** labs are run only inside PortSwigger's own lab environment, as intended by PortSwigger. Which labs I actually completed is recorded in `portswigger-lab-log.md`.
- **OWASP Juice Shop:** optional. If used, only as a local instance on my own machine following its setup guide. It is intentionally vulnerable and must never be exposed to a network.

## Test data provenance

All data is synthetic and created for this project: four demo users (`alice`, `bob`, `carol`, `dave`), their `<name>-demo-Passw0rd!` passwords, and a few example tickets. None is a real person, a real credential or private data. Signing keys are generated at start-up or set through an environment variable and are never committed (`.env.example` holds only a placeholder).

## Safety rules followed

- No real credentials, API keys or personal data in the repository, report or video.
- Mutation tests run on a temporary copy, never on the real code.
- Weaknesses are described and tested defensively. No exploit code is included.

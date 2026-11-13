# References

Access date: **13 November 2026** for sources opened during this review. Reference 20 retains its previously recorded **8 November 2026** date because it could not be opened during this review. "Used for" says what I took from each.

| # | Title | URL | Used for |
|---|-------|-----|----------|
| 1 | PortSwigger. *Web Security Academy: Free Online Training from PortSwigger* | https://portswigger.net/web-security | Background on authentication and access-control attacks; lab practice (see `docs/portswigger-lab-log.md`) |
| 2 | OWASP. *Juice Shop - Insecure Web Application for Security Training* | https://owasp.org/www-project-juice-shop/ | Awareness of an intentionally vulnerable local target; scope rules |
| 3 | OWASP. *Web Security Testing Guide* | https://owasp.org/www-project-web-security-testing-guide/ | Test planning and how to record evidence |
| 4 | OWASP WSTG. *Testing for Bypassing Authorization Schema* | https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/02-Testing_for_Bypassing_Authorization_Schema | Designing denied-request tests for role checks |
| 5 | OWASP. *OWASP Cheat Sheet Series* | https://cheatsheetseries.owasp.org/ | Index for the sheets below |
| 6 | OWASP. *OWASP Top 10 API Security Risks - 2023* | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ | Threat list (broken object and function-level authorisation, resource consumption) |
| 7 | FastAPI. *OAuth2 with Password (and hashing), Bearer with JWT tokens* | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ | Structure of login and bearer-token dependency |
| 8 | PyJWT. *Welcome to PyJWT* | https://pyjwt.readthedocs.io/en/stable/ | Pinning algorithms and requiring claims |
| 9 | IETF. *RFC 8725: JSON Web Token Best Current Practices* | https://www.rfc-editor.org/rfc/rfc8725 | Rejecting `alg: none`, validating issuer and expiry |
| 10 | IETF. *RFC 6750: Bearer Token Usage* | https://www.rfc-editor.org/rfc/rfc6750 | `WWW-Authenticate: Bearer` on 401 |
| 11 | IETF. *RFC 6585: Additional HTTP Status Codes* | https://www.rfc-editor.org/rfc/rfc6585 | 429 Too Many Requests |
| 12 | IETF. *RFC 7914: The scrypt Password-Based Key Derivation Function* | https://www.rfc-editor.org/info/rfc7914/ | Password hashing parameters |
| 13 | OWASP. *Password Storage* | https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html | Choosing scrypt and salting |
| 14 | OWASP. *Authorization* | https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html | Deny by default, check on every request |
| 15 | OWASP. *Input Validation* | https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html | Allow-list validation, length limits |
| 16 | OWASP. *Mass Assignment* | https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html | Rejecting unknown fields |
| 17 | OWASP. *REST Security* | https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html | Content-Type checks, rate limiting, error handling |
| 18 | OWASP. *Logging* | https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html | What not to log |
| 19 | NIST. *SP 800-228: Guidelines for API Protection for Cloud-Native Systems* (updated 13 Mar 2026) | https://csrc.nist.gov/pubs/sp/800/228/upd1/final | API controls overview |
| 20 | Uvicorn. *Settings (proxy headers, forwarded-allow-ips)* | https://www.uvicorn.org/settings/ | Explaining the proxy-header behaviour found in the demo |
| 21 | RedKross Task 2 Starter Pack. *01_WEB_SECURITY* (shared resource folder) | https://drive.google.com/drive/folders/15PW1L567EOd1lEd0dv5g4oUSoHdBvk1o?usp=sharing | Mock validation, output-handling, role-access, and health-response fixtures used only as a coverage cross-check; not findings about this project |

## Link check notes

- Reference 4's URL redirects to the general WSTG landing page, so its specific page title could not be confirmed.
- Reference 20 could not be opened because `www.uvicorn.org` did not resolve during this review. Its earlier recorded access date is retained and still needs your confirmation.

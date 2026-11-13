# PortSwigger Web Security Academy: lab log

Source: https://portswigger.net/web-security. Only labs I actually completed are listed. Labs were done in PortSwigger's own lab environment, as intended.

**At least 2 completed labs are confirmed by the screenshots provided. Academy profile total:** `<ENTER THE TOTAL SHOWN ON YOUR ACADEMY PROFILE>`. The screenshots confirm these two solved labs; they do not establish your account's overall total or completion dates.

| Date | Topic | Lab title | Level | Completed | One thing I learned (my words) | Link to my API |
|------|-------|-----------|-------|-----------|--------------------------------|----------------|
| 11 November 2026 | Access control / input validation | Bypassing access controls using email address parsing discrepancies | Expert | yes (screenshot-confirmed) | `<WRITE YOUR OWN SENTENCE>` | Strict allow-list validation (`app/models.py`): validate the exact value that will be used |
| 13 November 2026 | JWT attacks | JWT authentication bypass via algorithm confusion | Expert | yes (screenshot-confirmed) | `<WRITE YOUR OWN SENTENCE>` | Algorithm pinned to HS256 and required claims (`app/security.py`). My API has no public key or JWKS endpoint, so this exact attack does not apply; the defence is the same |

Note: the lab steps are PortSwigger's published solutions and are not copied here.

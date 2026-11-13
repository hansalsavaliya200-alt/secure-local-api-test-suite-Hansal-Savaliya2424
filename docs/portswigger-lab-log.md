# PortSwigger Web Security Academy: lab log

This log records the labs for which a title and completion details were provided or confirmed. It is not a complete list of all Academy activity. Labs are completed in PortSwigger's own lab environment.

**Reported Academy profile total:** 273 (provided by the project owner; not independently verified as the number of labs listed below).

| Date completed | Topic | Lab title | Level | Record | Project connection | Personal takeaway |
|---|---|---|---|---|---|---|
| 11 November 2026 | Access control / identifier parsing | Bypassing access controls using email address parsing discrepancies | Expert | Screenshot-confirmed | Related principle: validate identifiers consistently. This API uses usernames, not email addresses, and does not reproduce this lab. | `<WRITE YOUR OWN TAKEAWAY>` |
| 13 November 2026 | JWT attacks | JWT authentication bypass via algorithm confusion | Expert | Screenshot-confirmed | The API pins HS256 and requires token claims (`app/security.py`). It does not use public-key/JWKS verification, so do not claim that this lab's exact setup exists in the project. | `<WRITE YOUR OWN TAKEAWAY>` |

Add more entries only when you can provide the exact lab title and completion details. Do not copy PortSwigger's solution steps. Replace each takeaway placeholder with your own experience and wording before submission.

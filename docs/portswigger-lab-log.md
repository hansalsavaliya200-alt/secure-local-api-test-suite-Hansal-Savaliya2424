# PortSwigger Web Security Academy: lab log

Source: https://portswigger.net/web-security. Only labs I actually completed are listed. Labs were done in PortSwigger's own lab environment, as intended.

**Total completed:** `<WRITE THE NUMBER SHOWN ON YOUR ACADEMY PROFILE, e.g. 273>`. The labs below are the ones most relevant to this task.

| Date | Topic | Lab title | Level | Completed | One thing I learned (my words) | Link to my API |
|------|-------|-----------|-------|-----------|--------------------------------|----------------|
| `<DATE>` | Access control / input validation | Bypassing access controls using email address parsing discrepancies | Expert | yes | `<WRITE YOUR OWN SENTENCE>` | Strict allow-list validation (`app/models.py`): validate the exact value that will be used |
| `<DATE>` | JWT attacks | JWT authentication bypass via algorithm confusion | Expert | yes | `<WRITE YOUR OWN SENTENCE>` | Algorithm pinned to HS256 and required claims (`app/security.py`). My API has no public key or JWKS endpoint, so this exact attack does not apply; the defence is the same |
| `<DATE>` | | `<add more labs you finished>` | | | | |

Note: the lab steps are PortSwigger's published solutions and are not copied here.

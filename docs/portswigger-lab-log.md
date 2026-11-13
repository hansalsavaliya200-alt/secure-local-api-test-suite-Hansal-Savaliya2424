# PortSwigger Web Security Academy: lab log

Source: https://portswigger.net/web-security. Only labs I actually completed are listed. Labs were done in PortSwigger's own lab environment, as intended.

**Academy profile total (provided by you): 273.** The screenshots confirm the two solved labs below; they do not establish additional lab titles or your personal takeaways.

| Date | Topic | Lab title | Level | Completed | One thing I learned (my words) | Link to my API |
|------|-------|-----------|-------|-----------|--------------------------------|----------------|
| 11 November 2026 | Access control / input validation | Bypassing access controls using email address parsing discrepancies | Expert | yes (screenshot-confirmed) | `<WRITE YOUR OWN SENTENCE>` | Strict allow-list validation (`app/models.py`): validate the exact value that will be used |
| 13 November 2026 | JWT attacks | JWT authentication bypass via algorithm confusion | Expert | yes (screenshot-confirmed) | `<WRITE YOUR OWN SENTENCE>` | Algorithm pinned to HS256 and required claims (`app/security.py`). My API has no public key or JWKS endpoint, so this exact attack does not apply; the defence is the same |

Note: the lab steps are PortSwigger's published solutions and are not copied here.

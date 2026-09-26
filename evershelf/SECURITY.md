# Security Policy

## Supported Versions

Only the latest released version of EverShelf receives security fixes.

| Version | Supported |
|---------|-----------|
| Latest (1.7.x) | ✅ |
| Older releases | ❌ |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report security issues privately via email:

**📧 evershelfproject@gmail.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Your GitHub username (optional — for credit)

I aim to acknowledge reports within **48 hours** and release a fix within **7 days** for critical issues.

## Scope

EverShelf is a **self-hosted** application. The security model assumes:

- It runs on a trusted private network (home LAN)
- Access from the internet requires the user to set up their own authentication layer (e.g. reverse proxy with Authelia, Nginx `auth_basic`)

Out-of-scope issues:
- Vulnerabilities that require physical access to the server
- Issues only affecting users who have not followed the security recommendations in the README
- Denial-of-service attacks on the demo server

## Security Features

- API keys stored server-side in `.env`, never sent to the browser
- `get_settings` returns only boolean flags (`gemini_key_set`), never raw key values
- Optional `SETTINGS_TOKEN` protects write operations (`hash_equals` to prevent timing attacks)
- `DEMO_MODE=true` blocks all write operations at the router level
- Parameterized SQL queries (PDO prepared statements) throughout
- Input validation and length limits on all user-supplied fields
- `.env` and `data/` directories denied via web server config (see README)

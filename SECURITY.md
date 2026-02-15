# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | ✅ Currently supported |

## Reporting a Vulnerability

If you discover a security vulnerability within Zen Downloader, please send an email to github@hengly.com. All security vulnerabilities will be promptly addressed.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## What to Expect

- Acknowledgment of your report within 24 hours
- Regular updates on the progress of fixing the vulnerability
- Credit in the security advisory (if desired)

## Security Best Practices

When using Zen Downloader:

1. **Only download content you have the right to download**
2. **Keep your yt-dlp updated** - Run `pip install -U yt-dlp` regularly
3. **Use in a secure environment** - Don't expose the server to untrusted networks without proper authentication

## Scope

This security policy applies to:
- The main application code (app.py)
- The frontend (static/, templates/)
- The setup and run scripts

This policy does NOT cover:
- Third-party dependencies (yt-dlp, Flask, etc.)
- The websites being downloaded from
- User-downloaded content

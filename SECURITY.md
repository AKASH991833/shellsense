# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of ShellSense AI seriously. If you believe you have found a security vulnerability, please report it to us following these guidelines:

### How to Report

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Email details to security@shellsense.ai (or use the GitHub Security Advisory "Report a Vulnerability" tab).
3. Include as much detail as possible:
   - Type of vulnerability
   - Full paths of affected source files
   - Steps to reproduce
   - Proof of concept (if available)
   - Impact description

### What to Expect

- You will receive an acknowledgment within 48 hours.
- We will investigate and provide a timeline for a fix.
- We will notify you when the vulnerability is fixed.
- Public disclosure will be coordinated after the fix is released.

## Scope

The following areas are in scope for security research:

- API key storage and handling
- Plugin sandboxing and isolation
- Command execution safety
- Path traversal protection
- Sensitive data handling
- Configuration file permissions
- Prompt injection resistance
- Marketplace signature verification
- Session/conversation data storage

## Security Measures

ShellSense AI implements the following security measures:

- API keys are read from environment variables when available
- Plugin execution is sandboxed with restricted import access
- Config directory uses restrictive permissions (0700)
- Conversation history is stored locally only
- Telemetry is disabled by default
- No data is sent to external services without explicit consent

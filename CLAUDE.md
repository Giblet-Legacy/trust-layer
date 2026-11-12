# Forge Stack Context — P11 Trust

CLAUDE.md — Context briefing for AI assistants working in this repository.

## The Immutable Rule
Never rewrite a primitive. Add a layer.

## Dual-Device Workflow
We build on an S24 (Termux) and a laptop (VS Code). State is confirmed, never assumed. Always use LF line endings. Commit messages must be clear. We use the Good/Bad/Ugly CHANGELOG format (latest at top).

## Header Discipline
Every file MUST have a top header paragraph explaining its function.
Every function MUST have a numbered header.

## P11 Architecture Specifics
- Depends on `weight` (P10).
- The fusion engine: combines observations and parameters into a final λ.
- No file I/O, no crypto, no database. Pure math over given inputs.
- Lambda is never stored as authoritative state.

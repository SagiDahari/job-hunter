"""Service layer (ADR-003): use-case orchestration.

Coordinates domain logic and repositories to fulfil a use case. May import
``domain`` and ``repositories``; must not import ``api``.
"""

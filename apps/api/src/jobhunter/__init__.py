"""JobHunter AI backend package.

The application is organized into layers (see ADR-003):

- ``api``          HTTP routers — thin, request/response only.
- ``services``     use-case orchestration.
- ``domain``       pure business models and rules (no framework imports).
- ``repositories`` data access, one per aggregate.

Submodules are added incrementally across Batch 01 PRs.
"""

__version__ = "0.0.0"

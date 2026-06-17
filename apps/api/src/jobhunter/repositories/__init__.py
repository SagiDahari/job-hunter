"""Repository layer (ADR-003): all data access, one per aggregate.

The only layer that issues SQL. Concrete repositories and the SQLAlchemy base arrive
in PR-005. May import ``domain``; must not import ``services`` or ``api``.
"""

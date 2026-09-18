"""
app.db – Thin re-export of bhoomi_common.db utilities.

All services share the same async engine/session factory pattern from the
shared library.  Import from here so that each service has a single,
consistent dependency-injection target.
"""

from bhoomi_common.db import (  # noqa: F401
    check_db_health,
    close_db,
    get_db,
    get_engine,
    init_db,
)

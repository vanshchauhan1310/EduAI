"""
User roles for the governance hierarchy.
"""

from enum import Enum


class Role(str, Enum):
    DEO     = "DEO"      # District Education Officer
    MEO     = "MEO"      # Mandal Education Officer
    BEO     = "BEO"      # Block Education Officer
    HM      = "HM"       # Headmaster / Principal
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT  = "PARENT"


# Convenience groupings used by route guards.
GOVERNANCE_ROLES = {Role.DEO, Role.MEO, Role.BEO, Role.HM}
STAFF_ROLES      = GOVERNANCE_ROLES | {Role.TEACHER}
ALL_ROLES        = set(Role)

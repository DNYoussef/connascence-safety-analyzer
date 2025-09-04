
from enum import Enum

class WaiverStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Waiver:
    """Policy waiver."""
    def __init__(self, violation_id, reason, status=WaiverStatus.PENDING):
        self.violation_id = violation_id
        self.reason = reason
        self.status = status

class WaiverSystem:
    """Waiver management system."""
    def __init__(self):
        self.waivers = []
        
    def request_waiver(self, violation_id, reason):
        waiver = Waiver(violation_id, reason)
        self.waivers.append(waiver)
        return waiver

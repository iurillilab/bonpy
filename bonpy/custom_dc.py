from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExperimentMetadata:
    timestamp: datetime
    animal_id: str
    exp_id: str

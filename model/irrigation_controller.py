import json
import random
import time


class IrrigationController:
    """
    Simula il controller di irrigazione di una zona del vigneto.
    Funziona sia come sensore (batteria, stato attuale)
    sia come attuatore (ON/OFF, livello, programmazione).
    Livelli di irrigazione: basso, medio, alto.
    Tipi di irrigazione: continua, a rotazione.
    """

    LEVEL_LOW = "low"
    LEVEL_MEDIUM = "medium"
    LEVEL_HIGH = "high"

    TYPE_CONTINUOUS = "continuous"
    TYPE_ROTATION = "rotation"

    def __init__(self, zone_id):
        self.zone_id = zone_id
        self.is_active = False
        self.irrigation_level = self.LEVEL_LOW
        self.irrigation_type = self.TYPE_ROTATION
        self.battery_level = 100.0
        self.timestamp = int(time.time())

    def activate(self, level=LEVEL_MEDIUM, irrigation_type=TYPE_ROTATION):
        self.is_active = True
        self.irrigation_level = level
        self.irrigation_type = irrigation_type
        self.battery_level = max(0.0, round(self.battery_level - random.uniform(0.0, 0.3), 2))
        self.timestamp = int(time.time())

    def deactivate(self):
        self.is_active = False
        self.timestamp = int(time.time())

    def set_level(self, level):
        if level in [self.LEVEL_LOW, self.LEVEL_MEDIUM, self.LEVEL_HIGH]:
            self.irrigation_level = level
            self.timestamp = int(time.time())

    def update_status(self):
        self.battery_level = max(0.0, round(self.battery_level - random.uniform(0.0, 0.3), 2))
        self.timestamp = int(time.time())
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

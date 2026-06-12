
import json


class ZoneDescriptor:
    """
    Rappresenta una zona del vigneto (Smart Object).
    Pubblicato come messaggio retained su: vigneto/<zone_id>/info
    """

    def __init__(self, zone_id, zone_name, producer, software_version):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.producer = producer
        self.software_version = software_version

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

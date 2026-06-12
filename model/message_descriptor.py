
import json
import time


class MessageDescriptor:
    """
    Tipologia generica per messaggi di telemetria o comandi.
    Contiene: tipo di messaggio, payload e timestamp.
    """

    def __init__(self, message_type, value):
        self.message_type = message_type
        self.value = value
        self.timestamp = int(time.time())

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

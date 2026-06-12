
import json
import random
import time


class EnvironmentalSensor:
    """
    Simula il sensore ambientale di una zona del vigneto.
    Misura: temperatura, umidità, luminosità, velocità del vento,
    indice UV, precipitazioni, PM10 e livello della batteria.
    """

    TEMP_MIN = 10.0
    TEMP_MAX = 40.0
    HUMIDITY_MIN = 20.0
    HUMIDITY_MAX = 95.0
    LUMINOSITY_MIN = 0.0
    LUMINOSITY_MAX = 100000.0
    WIND_MIN = 0.0
    WIND_MAX = 80.0
    UV_MIN = 0.0
    UV_MAX = 11.0
    RAINFALL_MIN = 0.0
    RAINFALL_MAX = 30.0
    PM10_MIN = 5.0
    PM10_MAX = 150.0

    def __init__(self, zone_id):
        self.zone_id = zone_id
        self.temperature = 0.0
        self.humidity = 0.0
        self.luminosity = 0.0
        self.wind_speed = 0.0
        self.uv_index = 0.0
        self.rainfall = 0.0
        self.pm10 = 0.0
        self.battery_level = 100.0
        self.timestamp = int(time.time())
        self.update_measurements()

    def update_measurements(self):
        self.temperature = round(random.uniform(self.TEMP_MIN, self.TEMP_MAX), 2)
        self.humidity = round(random.uniform(self.HUMIDITY_MIN, self.HUMIDITY_MAX), 2)
        self.luminosity = round(random.uniform(self.LUMINOSITY_MIN, self.LUMINOSITY_MAX), 2)
        self.wind_speed = round(random.uniform(self.WIND_MIN, self.WIND_MAX), 2)
        self.uv_index = round(random.uniform(self.UV_MIN, self.UV_MAX), 2)
        self.rainfall = round(random.uniform(self.RAINFALL_MIN, self.RAINFALL_MAX), 2)
        self.pm10 = round(random.uniform(self.PM10_MIN, self.PM10_MAX), 2)
        # La batteria si scarica lentamente
        self.battery_level = max(0.0, round(self.battery_level - random.uniform(0.0, 0.5), 2))
        self.timestamp = int(time.time())

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

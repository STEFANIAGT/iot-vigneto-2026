# Vigneto Intelligente - Zone Smart Object Emulator
# Emula una zona del vigneto con sensore ambientale e controller di irrigazione.
#
# Topic:
#   vigneto/<zone_id>/info                          (retained) -> ZoneDescriptor
#   vigneto/<zone_id>/sensor/environmental          (QoS 0)    -> EnvironmentalSensor
#   vigneto/<zone_id>/sensor/irrigation             (QoS 0)    -> IrrigationController
#   vigneto/<zone_id>/command/irrigation            (sub)      -> comandi dal DCM

import paho.mqtt.client as mqtt
import time
import json
from model.zone_descriptor import ZoneDescriptor
from model.environmental_sensor import EnvironmentalSensor
from model.irrigation_controller import IrrigationController
from conf.mqtt_conf_params import MqttConfigurationParameters


# CONFIGURAZIONE DELLA ZONA

ZONE_ID = "zona-01"
ZONE_NAME = "Zona Nord - Pinot Nero"
TELEMETRY_INTERVAL_SEC = 5      # intervallo pubblicazione telemetria
MESSAGE_LIMIT = 1000            # numero massimo messaggi (0 = infinito)


# MQTT CALLBACKS

def on_connect(client, userdata, flags, rc):
    print(f"[{ZONE_ID}] Connected to broker - result code: {rc}")

    # Sottoscrizione ai comandi di irrigazione per questa zona

    command_topic = "{0}/{1}/{2}/{3}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        ZONE_ID,
        MqttConfigurationParameters.COMMAND_TOPIC,
        MqttConfigurationParameters.IRRIGATION_TOPIC
    )
    client.subscribe(command_topic)
    print(f"[{ZONE_ID}] Subscribed to commands: {command_topic}")

    # Pubblica il descrittore della zona (retained)
    publish_zone_info()


def on_message(client, userdata, message):
    """Gestisce i comandi di irrigazione provenienti dal DCM."""
    message_payload = message.payload.decode("utf-8")
    print(f"[{ZONE_ID}] Command received on {message.topic}: {message_payload}")

    try:
        command = json.loads(message_payload)
        action = command.get("action")

        if not action:
            print(f"[{ZONE_ID}] Invalid command: missing 'action'")
            return

        if action == "activate":
            level = command.get("level", IrrigationController.LEVEL_MEDIUM)
            irr_type = command.get("type", IrrigationController.TYPE_ROTATION)
            irrigation_controller.activate(level, irr_type)
            print(f"[{ZONE_ID}] Irrigation ACTIVATED - level: {level}, type: {irr_type}")

        elif action == "deactivate":
            irrigation_controller.deactivate()
            print(f"[{ZONE_ID}] Irrigation DEACTIVATED")

        elif action == "set_level":
            level = command.get("level", IrrigationController.LEVEL_MEDIUM)
            irrigation_controller.set_level(level)
            print(f"[{ZONE_ID}] Irrigation level set to: {level}")

        else:
            print(f"[{ZONE_ID}] Unknown command action: {action}")

    except Exception as e:
        print(f"[{ZONE_ID}] Error processing command: {e}")

# FUNZIONI DI PUBBLICAZIONE

def publish_zone_info():
    """Pubblica il ZoneDescriptor come messaggio retained."""
    target_topic = "{0}/{1}/{2}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        zone_descriptor.zone_id,
        MqttConfigurationParameters.INFO_TOPIC
    )
    payload = zone_descriptor.to_json()
    mqtt_client.publish(target_topic, payload, qos=1, retain=True)
    print(f"[{ZONE_ID}] Zone Info Published (retained): Topic: {target_topic} Payload: {payload}")


def publish_environmental_data():
    """Pubblica la telemetria del sensore ambientale."""
    environmental_sensor.update_measurements()

    target_topic = "{0}/{1}/{2}/{3}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        ZONE_ID,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.ENVIRONMENTAL_TOPIC
    )
    payload = environmental_sensor.to_json()
    mqtt_client.publish(target_topic, payload, qos=0, retain=False)
    print(f"[{ZONE_ID}] Environmental Data Published: Topic: {target_topic} Payload: {payload}")

def publish_irrigation_status():
    """Pubblica lo stato del controller di irrigazione."""

    # Aggiorna lo stato interno (scarica batteria, aggiorna timer, ecc.)
    irrigation_controller.update_status()   # <-- AGGIUNTA QUI

    target_topic = "{0}/{1}/{2}/{3}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        ZONE_ID,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.IRRIGATION_TOPIC
    )
    payload = irrigation_controller.to_json()
    mqtt_client.publish(target_topic, payload, qos=0, retain=False)
    print(f"[{ZONE_ID}] Irrigation Status Published: Topic: {target_topic} Payload: {payload}")

# MAIN

# Creazione modelli Smart Object
zone_descriptor = ZoneDescriptor(
    zone_id=ZONE_ID,
    zone_name=ZONE_NAME,
    producer="Vigneto-Intelligente-UNIMORE",
    software_version="1.0.0"
)

environmental_sensor = EnvironmentalSensor(zone_id=ZONE_ID)
irrigation_controller = IrrigationController(zone_id=ZONE_ID)

# Creazione client MQTT
client_id = f"vigneto-zone-emulator-{ZONE_ID}"
mqtt_client = mqtt.Client(client_id)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
# username e password vengono passati al client MQTT
mqtt_client.username_pw_set(
    MqttConfigurationParameters.MQTT_USERNAME,
    MqttConfigurationParameters.MQTT_PASSWORD
)

print(f"[{ZONE_ID}] Connecting to {MqttConfigurationParameters.BROKER_ADDRESS}:{MqttConfigurationParameters.BROKER_PORT} ...")
mqtt_client.connect(MqttConfigurationParameters.BROKER_ADDRESS, MqttConfigurationParameters.BROKER_PORT)

mqtt_client.loop_start()

# Loop principale di telemetria
message_count = 0
while MESSAGE_LIMIT == 0 or message_count < MESSAGE_LIMIT:
        if environmental_sensor.battery_level <= 0:
        print(f"[{ZONE_ID}] Batteria esaurita - sensore spento")
        break
    publish_environmental_data()
    publish_irrigation_status()
    message_count += 1
    time.sleep(TELEMETRY_INTERVAL_SEC)

mqtt_client.loop_stop()
print(f"[{ZONE_ID}] Emulator stopped after {message_count} messages.")

# Vigneto Intelligente - Data Collector & Manager (DCM)
# Si sottoscrive a tutte le zone, riceve la telemetria, applica le regole intelligenti
# e invia comandi ai controller di irrigazione.
#
# Subscriptions:
#   vigneto/+/info                         -> ZoneDescriptor (retained)
#   vigneto/+/sensor/environmental         -> Dati del sensore ambientale
#   vigneto/+/sensor/irrigation            -> Stato del controller di irrigazione
#
# Commands published:
#   vigneto/<zone_id>/command/irrigation   -> Comando JSON ON/OFF/set_level
#
# Intelligent Rules applied:
#   Regola 1 – Stress Idrico: umidità < 30% E pioggia < 2mm → attiva irrigazione HIGH
#   Regola 2 – Rischio Fungino: umidità > 85% E temperatura > 20°C → disattiva irrigazione + alert
#   Regola 3 – Fertilizzazione: temperatura 15–25°C E umidità 50–70% E UV < 5 → invia notifica
#   Regola 4 – Critica: batteria < 10% → invia avviso di batteria critica

import paho.mqtt.client as mqtt
import json
import time
from model.zone_descriptor import ZoneDescriptor
from model.environmental_sensor import EnvironmentalSensor
from model.irrigation_controller import IrrigationController
from conf.mqtt_conf_params import MqttConfigurationParameters


#  Soglie delle regole

WATER_STRESS_HUMIDITY_THRESHOLD = 30.0    # %  - sotto questo valore = stress idrico
WATER_STRESS_RAINFALL_THRESHOLD = 2.0     # mm - sotto questo valore = stress idrico
FUNGAL_RISK_HUMIDITY_THRESHOLD = 85.0     # %  - sopra questo valore = rischio fungino
FUNGAL_RISK_TEMP_THRESHOLD = 20.0         # °C - sopra questo valore = rischio fungino
FERTILIZATION_TEMP_MIN = 15.0             # °C
FERTILIZATION_TEMP_MAX = 25.0             # °C
FERTILIZATION_HUMIDITY_MIN = 50.0         # %
FERTILIZATION_HUMIDITY_MAX = 70.0         # %
FERTILIZATION_UV_MAX = 5.0                # UV  - indice UV massimo per concimazione
BATTERY_CRITICAL_THRESHOLD = 10.0         # %


# Memorizzazione dello stato

# zone_id -> ultimi dati del sensore ambientale (dict)
zone_environmental_data = {}

# zone_id -> ultimi dati del controller di irrigazione (dict)
zone_irrigation_data = {}

# zone_id -> descrittore della zona
zone_descriptors = {}

# Registro storico degli eventi:
# lista di dict con: timestamp, zone_id, event_type, detail
event_log = []

# Timestamp dell'ultimo riepilogo stampato
last_log_print_time = time.time()

last_time_policy_activation = {}  # zone_id -> ora dell'ultima attivazione

# MQTT callbacks: funzioni richiamate automaticamente dal client MQTT
# quando avvengono eventi come connessione al broker o ricezione di messaggi.

def on_connect(client, userdata, flags, rc):
    # Messaggio di log che conferma la connessione al broker MQTT
    print(f"[DCM] Connected to broker - result code: {rc}")

    # Sottoscrizione a tutte le informazioni delle zone (messaggi retained)
    info_topic = "{0}/+/{1}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.INFO_TOPIC
    )
    mqtt_client.subscribe(info_topic)
    # Messaggio di log che conferma l’avvenuta sottoscrizione al topic MQTT
    print(f"[DCM] Subscribed to: {info_topic}")

    # Sottoscrizione ai dati dei sensori ambientali di tutte le zone
    env_topic = "{0}/+/{1}/{2}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.ENVIRONMENTAL_TOPIC
    )
    mqtt_client.subscribe(env_topic)
    print(f"[DCM] Subscribed to: {env_topic}")

# Sottoscrizione ai dati sullo stato dell’irrigazione di tutte le zone
irr_topic = "{0}/+/{1}/{2}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.IRRIGATION_TOPIC
    )
    mqtt_client.subscribe(irr_topic)
    print(f"[DCM] Subscribed to: {irr_topic}")

def on_message(client, userdata, message):
    message_payload = str(message.payload.decode("utf-8"))
    topic = message.topic

    # Instrada verso il gestore corretto in base al topic
    info_filter = "{0}/+/{1}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.INFO_TOPIC
    )
    env_filter = "{0}/+/{1}/{2}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.ENVIRONMENTAL_TOPIC
    )
    irr_filter = "{0}/+/{1}/{2}".format(
        MqttConfigurationParameters.BASIC_TOPIC,
        MqttConfigurationParameters.SENSOR_TOPIC,
        MqttConfigurationParameters.IRRIGATION_TOPIC
    )

    if mqtt.topic_matches_sub(info_filter, topic):
        handle_zone_info_message(topic, message_payload)
    elif mqtt.topic_matches_sub(env_filter, topic):
        handle_environmental_message(topic, message_payload)
    elif mqtt.topic_matches_sub(irr_filter, topic):
        handle_irrigation_message(topic, message_payload)
    else:
        print(f"[DCM] Unmanaged topic: {topic}")
        # Messaggio di log per segnalare che il topic ricevuto non è gestito dal DCM

 # Stampa il riepilogo del log ogni EVENT_LOG_PRINT_INTERVAL_SEC secondi
    if time.time() - last_log_print_time >= EVENT_LOG_PRINT_INTERVAL_SEC:
        print_event_log_summary()
        last_log_print_time = time.time()

# Gestori dei messaggi: funzioni che elaborano i payload ricevuti dai vari topic MQTT

def handle_zone_info_message(topic, payload):
    """Gestisce i messaggi retained di tipo ZoneDescriptor."""
    try:
        data = json.loads(payload)
        zone = ZoneDescriptor(**data)
        zone_descriptors[zone.zone_id] = zone
        # Messaggio di log che conferma la registrazione della zona tramite messaggio retained
        print(f"[DCM] Zone registered (retained:{True}): ID={zone.zone_id} Name={zone.zone_name} "
              f"Producer={zone.producer} Version={zone.software_version}")
    except Exception as e:
        print(f"[DCM] Error parsing zone info from {topic}: {e}")
        # Messaggio di log per segnalare un errore nel processo di analisi strutturata
        # delle informazioni della zona

def handle_environmental_message(topic, payload):
    """Gestisce la telemetria dei sensori ambientali e applica le regole intelligenti."""
    try:
        data = json.loads(payload)
        zone_id = extract_zone_id_from_topic(topic)
        zone_environmental_data[zone_id] = data

        print(f"[DCM] Environmental Data - Zone: {zone_id} | "
              f"Temp: {data['temperature']}°C | "
              f"Humidity: {data['humidity']}% | "
              f"Rainfall: {data['rainfall']}mm | "
              f"UV: {data['uv_index']} | "
              f"Battery: {data['battery_level']}%")

        # Applica tutte le regole intelligenti
        apply_water_stress_rule(zone_id, data)
        apply_fungal_risk_rule(zone_id, data)
        apply_fertilization_rule(zone_id, data)
        apply_critical_battery_rule(zone_id, data)

    except Exception as e:
        print(f"[DCM] Error processing environmental data from {topic}: {e}")


def handle_irrigation_message(topic, payload):
    """Gestisce gli aggiornamenti di stato del regolatore di irrigazione."""
    try:
          data = json.loads(payload)
        zone_id = extract_zone_id_from_topic(topic)
        zone_irrigation_data[zone_id] = data

        status = "ACTIVE" if data["is_active"] else "INACTIVE"
        print(f"[DCM] Irrigation Status - Zone: {zone_id} | "
              f"Status: {status} | "
              f"Level: {data['irrigation_level']} | "
              f"Type: {data['irrigation_type']} | "
              f"Battery: {data['battery_level']}%")

    except Exception as e:
        print(f"[DCM] Error processing irrigation data from {topic}: {e}")


# Regole intelligenti

def apply_water_stress_rule(zone_id, env_data):
    """
    Regola 1 – Stress Idrico: umidità < 30% E pioggia < 2mm → attiva irrigazione HIGH.
    """
    if (env_data["humidity"] < WATER_STRESS_HUMIDITY_THRESHOLD and
            env_data["rainfall"] < WATER_STRESS_RAINFALL_THRESHOLD):

        print(f"[DCM] RULE 1 - WATER STRESS detected in Zone {zone_id}! "
              f"Humidity={env_data['humidity']}% Rainfall={env_data['rainfall']}mm "
              f"-> Activating HIGH irrigation")

        send_irrigation_command(zone_id, {
            "action": "activate",
            "level": IrrigationController.LEVEL_HIGH,
            "type": IrrigationController.TYPE_CONTINUOUS,
            "reason": "water_stress"
        })

        log_event(zone_id, "STRESS_IDRICO",
              f"Humidity={env_data['humidity']} Rainfall={env_data['rainfall']}")
...

def apply_fungal_risk_rule(zone_id, env_data):
    """
    Regola 2 – Rischio Fungino: umidità > 85% E temperatura > 20°C → disattiva irrigazione + alert.
    """
    if (env_data["humidity"] > FUNGAL_RISK_HUMIDITY_THRESHOLD and
            env_data["temperature"] > FUNGAL_RISK_TEMP_THRESHOLD):

        print(f"[DCM] RULE 2 - FUNGAL RISK detected in Zone {zone_id}! "
              f"Humidity={env_data['humidity']}% Temp={env_data['temperature']}°C "
              f"-> Deactivating irrigation")

        send_irrigation_command(zone_id, {
            "action": "deactivate",
            "reason": "fungal_risk"
        })

        log_event(zone_id, "RISCHIO_FUNGINO",
              f"Humidity={env_data['humidity']} Temp={env_data['temperature']}")


def apply_fertilization_rule(zone_id, env_data):
    """
    Regola 3 – Fertilizzazione: temperatura 15–25°C E umidità 50–70% E UV < 5 → invia notifica.
    """
    if (FERTILIZATION_TEMP_MIN <= env_data["temperature"] <= FERTILIZATION_TEMP_MAX and
            FERTILIZATION_HUMIDITY_MIN <= env_data["humidity"] <= FERTILIZATION_HUMIDITY_MAX and
            env_data["uv_index"] < FERTILIZATION_UV_MAX):

        print(f"[DCM] RULE 3 - FAVORABLE FERTILIZATION CONDITIONS in Zone {zone_id}! "
              f"Temp={env_data['temperature']}°C Humidity={env_data['humidity']}% "
              f"UV={env_data['uv_index']} -> Fertilization recommended")

        log_event(zone_id, "CONCIMAZIONE_CONSIGLIATA",
                  f"Temp={env_data['temperature']}°C Umidità={env_data['humidity']}% UV={env_data['uv_index']}")




def apply_critical_battery_rule(zone_id, env_data):
    """
    Regola 4 – Critica: batteria < 10% → invia avviso di batteria critica.
    """
    if env_data["battery_level"] < BATTERY_CRITICAL_THRESHOLD:
        print(f"[DCM] RULE 4 - CRITICAL BATTERY in Zone {zone_id}! "
              f"Battery={env_data['battery_level']}% -> Maintenance required!")

        log_event(zone_id, "BATTERIA_CRITICA",
          f"Battery={env_data['battery_level']}")

# REGISTRO STORICO EVENTI
def log_event(zone_id, event_type, detail):
    """Aggiunge un evento al registro storico."""
    event = {
        "timestamp": int(time.time()),
        "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "zone_id": zone_id,
        "event_type": event_type,
        "detail": detail
    }
    event_log.append(event)


def print_event_log_summary():
    """Stampa il riepilogo del registro storico degli eventi."""
    print("\n" + "=" * 70)
    print(f" RIEPILOGO EVENTI — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not event_log:
        print("  Nessun evento registrato.")
    else:
        # Conta gli eventi per tipo
        counts = {}
        for e in event_log:
            key = (e["zone_id"], e["event_type"])
            counts[key] = counts.get(key, 0) + 1

        print(f"  Totale eventi registrati: {len(event_log)}")
        print()

        # Stampa contatori per zona e tipo
        for (zone_id, event_type), count in sorted(counts.items()):
            print(f"  [{zone_id}]  {event_type:<30} x{count}")

        print()

        # Stampa gli ultimi 5 eventi
        print("  Ultimi 5 eventi:")
        for e in event_log[-5:]:
            print(f"  {e['timestamp_str']}  [{e['zone_id']}]  {e['event_type']}")
            print(f"    → {e['detail']}")

        # Stato attuale delle zone
        print()
        print("  Stato attuale delle zone:")
        for zone_id, env in zone_environmental_data.items():
            irr = zone_irrigation_data.get(zone_id, {})
            irr_status = "ATTIVA" if irr.get("is_active", False) else "INATTIVA"
            print(f"  [{zone_id}]  Temp: {env['temperature']}°C | "
                  f"Umidità: {env['humidity']}% | "
                  f"Batteria sensore: {env['battery_level']}% | "
                  f"Irrigazione: {irr_status}")

    print("=" * 70 + "\n")


# Modulo che invia i comandi: Gestore responsabile dell’invio dei comandi ai dispositivi/zone
...

# Raccolta di funzioni di utilità a supporto delle operazioni del DCM

def extract_zone_id_from_topic(topic):
    """Estrae lo zone_id dal topic: vigneto/<zone_id>/sensor/..."""
    parts = topic.split("/")
    return parts[4] if len(parts) > 4 else "unknown"


# Main
# Inizializzazione del client MQTT del DCM con il client_id configurato
client_id = MqttConfigurationParameters.DCM_CLIENT_ID
mqtt_client = mqtt.Client(client_id)
# Registrazione delle callback per connessione e gestione dei messaggi
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
# username e password vengono passati al client MQTT
mqtt_client.username_pw_set(
    MqttConfigurationParameters.MQTT_USERNAME,
    MqttConfigurationParameters.MQTT_PASSWORD
)

# Log di avvio connessione verso il broker MQTT
print(f"[DCM] Connecting to {MqttConfigurationParameters.BROKER_ADDRESS}:{MqttConfigurationParameters.BROKER_PORT} ...")
# Connessione al broker MQTT
mqtt_client.connect(MqttConfigurationParameters.BROKER_ADDRESS, MqttConfigurationParameters.BROKER_PORT)

# Ciclo bloccante che gestisce il traffico MQTT e richiama le callback registrate
mqtt_client.loop_forever()

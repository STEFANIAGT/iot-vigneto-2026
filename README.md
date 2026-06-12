# iot-vigneto-2026
Sistema di monitoraggio e gestione intelligente del vigneto basato su sensori IoT e analisi dei dati.

<!-- omit in toc -->
# Vigneto Intelligente
### Smart Agriculture — Salute delle Piante e Irrigazione Automatizzata

<!-- omit in toc -->
### Intelligent Internet of Things — UNIMORE A.A. 2025/2026 — Prof. Marco Picone

---

<!-- omit in toc -->
# Indice

- [Descrizione dello Scenario](#descrizione-dello-scenario)
- [Architettura e Componenti Principali](#architettura-e-componenti-principali)
- [Modelli dei Dati](#modelli-dei-dati)
- [Protocolli e Comunicazione](#protocolli-e-comunicazione)
  - [Topic MQTT e Dati](#topic-mqtt-e-dati)
  - [Mapping Topic MQTT e Componenti](#mapping-topic-mqtt-e-componenti)
- [Regole Intelligenti — Data Collector \& Manager](#regole-intelligenti--data-collector--manager)
- [Struttura del Progetto](#struttura-del-progetto)
- [Come Eseguire il Progetto](#come-eseguire-il-progetto)
- [Divisione dei Compiti](#divisione-dei-compiti)
- [Studentesse](#studentesse)

---

# Descrizione dello Scenario

Il sistema **Vigneto Intelligente** è una soluzione IoT distribuita per la gestione intelligente di un vigneto. Il sistema monitora in tempo reale le condizioni ambientali di più zone del vigneto e valuta automaticamente lo stato di salute delle piante, identificando situazioni di stress idrico, rischio di malattie fungine (peronospora, oidio, botrite) e condizioni favorevoli alla concimazione.

Ogni zona è equipaggiata con un **Sensore Ambientale** che misura temperatura, umidità, luminosità, velocità del vento, indice UV, precipitazioni, PM10 e livello della batteria, e con un **Regolatore di Irrigazione** che funge sia da sensore (feedback sullo stato attuale) che da attuatore (ON/OFF, livello, policy orarie). Un **Data Collector & Manager** centralizzato raccoglie tutta la telemetria, applica le regole decisionali intelligenti e invia i comandi di attuazione ai regolatori di irrigazione.

Il sistema è progettato per supportare **N zone** in modo concorrente, risultando scalabile da un piccolo vigneto a un impianto agricolo multi-zona di grandi dimensioni.

---

# Architettura e Componenti Principali

##  Architettura del Sistema
┌────────────────────────┐        MQTT        ┌──────────────────────────────┐
│   Sensore Ambientale   │ ─────────────────▶   Data Collector & Manager   
│        (per zona)      │                    │   • Raccolta dati            │
└────────────────────────┘                    │   • Analisi intelligente     │
                                              │   • Invio comandi attuatori  │
┌────────────────────────┐        MQTT        │   • Generazione eventi       │
│  Regolatore Irrigazione│ ◀─────────────────                              
│        (per zona)      │                                    
└────────────────────────┘                                   │
                                                             ▼
                                                    ┌───────────────────┐
                                                    │     Dashboard     │
                                                    └───────────────────┘



- **Livello Edge (Smart Object IoT di Zona)**
  - **Sensore Ambientale** (uno per zona):
    - **Temperatura**: valutazione dello stress termico
    - **Umidità**: rilevamento dello stress idrico e del rischio fungino
    - **Luminosità**: contesto per l'attività fotosintetica
    - **Velocità del vento**: stima dell'evapotraspirazione
    - **Indice UV**: monitoraggio della radiazione solare
    - **Precipitazioni**: misurazione dell'apporto idrico naturale
    - **PM10**: qualità dell'aria e contaminazione da polveri
    - **Livello batteria**: monitoraggio dello stato energetico del dispositivo
  - **Regolatore di Irrigazione** (uno per zona):
    - **Sensore**: stato di attivazione corrente, livello di irrigazione, tipo di irrigazione, livello batteria
    - **Attuatore**: attivazione ON/OFF, controllo del livello (low / medium / high), modalità (continuous / rotation), policy orarie

- **Livello di Connettività**
  - MQTT su TCP/IP verso il broker del laboratorio 

- **Livello Applicativo**
  - **Data Collector & Manager**: componente centrale che acquisisce la telemetria da tutte le zone, applica quattro regole intelligenti e invia i comandi di attuazione ai regolatori di irrigazione

---

# Modelli dei Dati

Tutti i timestamp sono rappresentati come Unix epoch time in secondi per garantire coerenza tra tutti i tipi di dati. La presenza del campo `timestamp` in ogni modello permette l'analisi delle serie temporali, la correlazione degli eventi e la gestione degli arrivi fuori ordine.

**Modello ZoneDescriptor**

Contiene i metadati di ogni Smart Object di zona. Pubblicato come messaggio retained in modo che il DCM e qualsiasi sottoscrittore tardivo possano sempre recuperare l'ultima registrazione della zona.

| **Campo** | **Tipo** | **Descrizione** |
|-----------|----------|-----------------|
| `zone_id` | String | Identificativo univoco della zona (es. `zona-01`) |
| `zone_name` | String | Nome leggibile della zona (es. `Zona Nord - Pinot Nero`) |
| `producer` | String | Nome del produttore del dispositivo |
| `software_version` | String | Versione del firmware/software (es. `1.0.0`) |

---

**Modello EnvironmentalSensor**

Raccoglie tutte le letture ambientali di una zona del vigneto in un dato istante. Usato dal DCM per valutare le condizioni di salute delle piante e attivare le regole di irrigazione.

| **Campo** | **Tipo** | **Descrizione** |
|-----------|----------|-----------------|
| `zone_id` | String | Identificativo della zona di riferimento |
| `temperature` | Double | Temperatura dell'aria (°C) |
| `humidity` | Double | Umidità relativa dell'aria (%) |
| `luminosity` | Double | Luminosità (lux) |
| `wind_speed` | Double | Velocità del vento (km/h) |
| `uv_index` | Double | Indice di radiazione UV (0–11) |
| `rainfall` | Double | Precipitazioni nel periodo (mm) |
| `pm10` | Double | Concentrazione di particolato (µg/m³) |
| `battery_level` | Double | Batteria residua (%, 0–100) |
| `timestamp` | Long | Timestamp Unix epoch (s) |

---

**Modello IrrigationController**

Rappresenta lo stato attuale dell'attuatore di irrigazione di una zona. Pubblicato periodicamente come telemetria e aggiornato alla ricezione di comandi dal DCM.

| **Campo** | **Tipo** | **Descrizione** |
|-----------|----------|-----------------|
| `zone_id` | String | Identificativo della zona di riferimento |
| `is_active` | Boolean | Indica se l'irrigazione è attualmente in corso |
| `irrigation_level` | String | Livello corrente: `low`, `medium`, `high` |
| `irrigation_type` | String | Modalità di irrigazione: `continuous`, `rotation` |
| `battery_level` | Double | Batteria residua (%, 0–100) |
| `timestamp` | Long | Timestamp Unix epoch (s) |

---

**Modello Comando di Irrigazione**

Inviato dal DCM al regolatore di irrigazione di una specifica zona per attivare, disattivare o modificare il livello di irrigazione.

| **Campo** | **Tipo** | **Descrizione** |
|-----------|----------|-----------------|
| `action` | String | Tipo di comando: `activate`, `deactivate`, `set_level` |
| `level` | String | Livello target (solo per `activate` / `set_level`): `low`, `medium`, `high` |
| `type` | String | Tipo di irrigazione (solo per `activate`): `continuous`, `rotation` |
| `reason` | String | Regola che ha generato il comando (es. `stress_idrico`, `rischio_fungino`) |

---

# Protocolli e Comunicazione

Lo scenario è principalmente associato all'**acquisizione di dati di telemetria** dagli Smart Object di zona verso il DCM centralizzato, con un flusso bidirezionale per i comandi di attuazione inviati ai regolatori di irrigazione. MQTT è il protocollo ideale per questo scenario per le seguenti motivazioni:

- Il modello publish/subscribe disaccoppia i produttori (emulatori di zona) dai consumatori (DCM)
- L'overhead ridotto è adatto a sensori alimentati a batteria nel campo
- Il supporto nativo per i messaggi retained (info di zona) e i livelli QoS adattati alla criticità dei dati
- Le sottoscrizioni con wildcard permettono al DCM di ricevere dati da tutte le zone con una singola sottoscrizione

Il broker MQTT utilizzato è il **broker del laboratorio UNIMORE**.

---

## Topic MQTT e Dati

**Topic Info di Zona**

- **Topic**: `vigneto/{zone_id}/info`
- **Payload**:
  ```json
  {
    "zone_id": "zona-01",
    "zone_name": "Zona Nord - Pinot Nero",
    "producer": "Vigneto-Intelligente-UNIMORE",
    "software_version": "1.0.0"
  }
  ```
- **Livello QoS**: 0
- **Retain Flag**: true (garantisce che il DCM e qualsiasi sottoscrittore tardivo ricevano sempre l'ultima registrazione della zona anche dopo una riconnessione)

---

**Topic Sensore Ambientale**

- **Topic**: `vigneto/{zone_id}/sensor/environmental`
- **Payload SenML+JSON**:
  ```json
  [
    { "n": "iot.vigneto.temperature",  "u": "Cel",   "v": 22.5,  "t": 1718000000 },
    { "n": "iot.vigneto.humidity",     "u": "%RH",   "v": 65.3,  "t": 1718000000 },
    { "n": "iot.vigneto.luminosity",   "u": "lux",   "v": 45000, "t": 1718000000 },
    { "n": "iot.vigneto.wind_speed",   "u": "km/h",  "v": 12.1,  "t": 1718000000 },
    { "n": "iot.vigneto.uv_index",     "u": "uv",    "v": 4.2,   "t": 1718000000 },
    { "n": "iot.vigneto.rainfall",     "u": "mm",    "v": 1.8,   "t": 1718000000 },
    { "n": "iot.vigneto.pm10",         "u": "ug/m3", "v": 28.0,  "t": 1718000000 },
    { "n": "iot.vigneto.battery",      "u": "%",     "v": 87.5,  "t": 1718000000 }
  ]
  ```
- **Livello QoS**: 0 (telemetria ad alta frequenza; la perdita occasionale è accettabile poiché la lettura successiva arriva a breve)
- **Retain Flag**: false (dati time-sensitive; mantenere letture obsolete potrebbe indurre il DCM in errore)

---

**Topic Stato Regolatore di Irrigazione**

- **Topic**: `vigneto/{zone_id}/sensor/irrigation`
- **Payload**:
  ```json
  {
    "zone_id": "zona-01",
    "is_active": true,
    "irrigation_level": "medium",
    "irrigation_type": "rotation",
    "battery_level": 91.0,
    "timestamp": 1718000000
  }
  ```
- **Livello QoS**: 0
- **Retain Flag**: false (lo stato attuale riflette l'ultimo comando ricevuto; mantenerlo potrebbe causare la ri-applicazione di uno stato obsoleto dopo una riconnessione)

---

**Topic Comandi di Irrigazione**

- **Topic**: `vigneto/{zone_id}/command/irrigation`
- **Payload**:
  ```json
  {
    "action": "activate",
    "level": "high",
    "type": "continuous",
    "reason": "stress_idrico"
  }
  ```
- **Livello QoS**: 0
- **Retain Flag**: false (i comandi sono time-sensitive; mantenerli causerebbe la ri-esecuzione alla riconnessione quando le condizioni potrebbero essere cambiate)

---

## Mapping Topic MQTT e Componenti

| Topic / Pattern | Scopo | Publisher | Subscriber | Note |
|-----------------|-------|-----------|------------|------|
| `vigneto/+/info` | Metadati della zona | Zone Emulator | Data Collector & Manager | Retained — consegnato ai sottoscrittori tardivi |
| `vigneto/+/sensor/environmental` | Telemetria ambientale di tutte le zone | Zone Emulator | Data Collector & Manager | QoS 0 — alta frequenza, wildcard |
| `vigneto/+/sensor/irrigation` | Stato irrigazione di tutte le zone | Zone Emulator | Data Collector & Manager | QoS 0 — aggiornamento stato, wildcard |
| `vigneto/{zone_id}/command/irrigation` | Comandi di attuazione | Data Collector & Manager | Zone Emulator | QoS 0 — payload JSON comando |

---

# Regole Intelligenti — Data Collector & Manager

Il DCM applica le seguenti quattro regole ad ogni messaggio di telemetria ambientale ricevuto:

| Regola | Nome | Condizione di Attivazione | Azione |
|--------|------|--------------------------|--------|
| **Regola 1** | Stress Idrico | `umidità < 30%` E `precipitazioni < 2 mm` | Attiva irrigazione a livello `high`, modalità `continuous` |
| **Regola 2** | Rischio Malattie Fungine | `umidità > 85%` E `temperatura > 20°C` | Disattiva irrigazione + genera evento di allerta |
| **Regola 3** | Condizioni per Concimazione | `15°C ≤ temperatura ≤ 25°C` E `50% ≤ umidità ≤ 70%` E `indice_uv < 5` | Genera evento: concimazione consigliata |
| **Regola 4** | Batteria Critica | `livello_batteria < 10%` | Genera evento: manutenzione necessaria |

Le Regole 1 e 2 si escludono a vicenda: in caso di attivazione simultanea (caso limite), la Regola 2 ha priorità poiché disattivare l'irrigazione è l'azione più sicura per la salute della pianta.

---

# Struttura del Progetto

```
iot-project-2026/
│
├── conf/
│   ├── __init__.py
│   └── mqtt_conf_params.py          # Indirizzo broker (155.185.4.4:7883), nomi topic
│
├── model/
│   ├── __init__.py
│   ├── zone_descriptor.py           # Info Smart Object di zona — pubblicato retained
│   ├── environmental_sensor.py      # Letture ambientali (temperatura, umidità, pioggia ...)
│   ├── irrigation_controller.py     # Attuatore irrigazione + sensore di stato
│   └── message_descriptor.py       # Wrapper generico per messaggi di telemetria
│
├── process/
│   ├── __init__.py
│   ├── zone_emulator.py             # Emulatore Smart Object di zona (producer + subscriber comandi)
│   └── data_collector_manager.py   # DCM — consumer + motore regole + publisher comandi
│
├── requirements.txt
└── README.md
```

---

# Come Eseguire il Progetto

### 1. Installare le dipendenze
```bash
pip install -r requirements.txt
```

### 2. Avviare il Data Collector & Manager
```bash
cd iot-project-2026
python process/data_collector_manager.py
```

### 3. Avviare uno o più emulatori di zona (ognuno in un terminale separato)

Ogni zona è identificata da `ZONE_ID` all'inizio del file `zone_emulator.py`. Per emulare più zone, aprire un nuovo terminale per ognuna e modificare `ZONE_ID` di conseguenza:

```bash
# Terminale 1 — ZONE_ID = "zona-01" (default)
python process/zone_emulator.py

# Terminale 2 — modificare ZONE_ID = "zona-02"
python process/zone_emulator.py

# Terminale 3 — modificare ZONE_ID = "zona-03"
python process/zone_emulator.py
```

Il DCM usa sottoscrizioni con wildcard (`vigneto/+/...`) quindi scopre e gestisce automaticamente qualsiasi numero di zone senza modifiche alla configurazione.

> **Broker**: 

1. Broker MQTT

Il sistema è compatibile con qualsiasi broker MQTT standard. Sono disponibili due opzioni:

Opzione A – Broker UNIMORE (usato a laboratorio)
Configuro mqtt_conf_params.py con le credenziali fornite a lezione:

Opzione B – HiveMQ Cloud (gratuito, niente installazione)
- Registrati su hivemq.com
- Crea un cluster gratuito e copia l'hostname
- Aggiorna mqtt_conf_params.py.

## Per la demo d'esame è stato utilizzato il broker UNIMORE del corso.

---

# Divisione dei Compiti

## Stefania Gatti — Monitoraggio e Analisi della Pianta

- Configurazione e gestione dei **Sensori Ambientali di Zona** (`model/environmental_sensor.py`)
- Implementazione della logica di:
  - Stress idrico
  - Rischio malattie fungine (peronospora, oidio, botrite)
  - Condizioni favorevoli per la concimazione
- Generazione degli eventi nel DCM:
  - Evento Stress Idrico → comando irrigazione HIGH
  - Evento Rischio Malattia → disattivazione irrigazione + allerta
  - Evento Concimazione Consigliata → notifica
- Integrazione dei dati nella dashboard (grafici, indicatori, storico)

## Giulia Tramontano — Automazione dell'Irrigazione e Gestione Attuatori

- Configurazione e gestione del **Regolatore di Irrigazione** (`model/irrigation_controller.py`)
- Implementazione delle regole di irrigazione intelligente:
  - ON/OFF automatico
  - Livelli Low / Medium / High
  - Policy orarie
- Gestione dei comandi MQTT verso gli attuatori (`process/zone_emulator.py` — lato comando)
- Visualizzazione dello stato dell'irrigazione nella dashboard

## Attività Svolte in Collaborazione

- Definizione dell'architettura generale del sistema
- Progettazione dei topic MQTT e dei messaggi JSON
- Sviluppo del **Data Collector & Manager** (`process/data_collector_manager.py`)
- Preparazione della demo
- Realizzazione delle slide e della documentazione finale

---

# Studentesse

| Nome | Email | GitHub |
|------|-----------|-------|
| Stefania Gatti | 331844@studenti.unimore.it |[@STEFANIAGT](https://github.com/STEFANIAGT) |
| Giulia Tramontano | 341080@studenti.unimore.it |[@giulyaaaa](https://github.com/giulyaaaa) |



 


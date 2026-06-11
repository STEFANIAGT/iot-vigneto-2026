# iot-vigneto-2026
Sistema di monitoraggio e gestione intelligente del vigneto basato su sensori IoT e analisi dei dati.

# Vigneto Intelligente – IoT Project 2026  
### Smart Agriculture – Monitoraggio della Pianta & Irrigazione Automatizzata  
**Intelligent Internet of Things — UNIMORE A.A. 2025/2026**  
**Prof. Marco Picone**

---

## Scenario Applicativo  
Il progetto simula un sistema IoT per la gestione intelligente di un vigneto.  
Ogni zona è dotata di:

- **Sensore Ambientale** → temperatura, umidità, luce, vento, UV, pioggia, PM10, batteria  
- **Regolatore di Irrigazione** → attuatore intelligente che riceve comandi dal DCM  
- **Data Collector & Manager (DCM)** → analizza i dati, applica regole intelligenti e invia comandi MQTT  

L’obiettivo è monitorare la salute della pianta e ottimizzare l’irrigazione in modo automatico.

---

##  Architettura del Sistema

-

## 📌 Scenario Applicativo  
Il progetto simula un sistema IoT per la gestione intelligente di un vigneto.  
Ogni zona è dotata di:

- **Sensore Ambientale** → temperatura, umidità, luce, vento, UV, pioggia, PM10, batteria  
- **Regolatore di Irrigazione** → attuatore intelligente che riceve comandi dal DCM  
- **Data Collector & Manager (DCM)** → analizza i dati, applica regole intelligenti e invia comandi MQTT  

L’obiettivo è monitorare la salute della pianta e ottimizzare l’irrigazione in modo automatico.

---

## 🧱 Architettura del Sistema

┌──────────────────────┐        MQTT        ┌──────────────────────────────┐
│  Sensore Ambientale  │ ─────────────────▶ │   Data Collector & Manager   │
│  (per zona)          │                    │   • Raccolta dati            │
└──────────────────────┘                    │   • Analisi intelligente     │
│   • Invio comandi attuatori  │
┌──────────────────────┐        MQTT        │   • Generazione eventi       │
│ Regolatore Irrigaz.  │ ◀───────────────── │                              │
│ (per zona)           │                    └──────────────┬──────────────┘
└──────────────────────┘                                   │
▼
┌───────────────────┐
│     Dashboard     │
└───────────────────┘
---

---

## 📡 Struttura Topic MQTT

| Topic | Tipo | Descrizione |
|-------|------|-------------|
| `vigneto/<zone_id>/info` | Retained | Informazioni statiche della zona |
| `vigneto/<zone_id>/telemetry` | Telemetria | Dati del sensore ambientale |
| `vigneto/<zone_id>/irrigation/state` | Telemetria | Stato del regolatore |
| `vigneto/<zone_id>/irrigation/cmd` | Comando | Comandi dal DCM al regolatore |

---

## 🧠 Regole Intelligenti (DCM)

- **Stress Idrico** → LOW / MEDIUM / HIGH  
- **Rischio Malattie Fungine** → alert  
- **Condizioni per Concimazione** → evento informativo  
- **Batteria Critica** → alert manutenzione  

---

## 📁 Struttura del Progetto

iot-vigneto-2026/
├── conf/
│   └── mqtt_conf_params.py
├── model/
│   ├── zone_descriptor.py
│   ├── environmental_sensor.py
│   ├── irrigation_controller.py
│   └── message_descriptor.py
├── process/
│   ├── zone_emulator.py
│   └── data_collector_manager.py
├── requirements.txt
└── README.md
---


---

## ▶️ Avvio del Sistema

### Setup e Avvio

1. Broker MQTT

Il sistema è compatibile con qualsiasi broker MQTT standard. Sono disponibili due opzioni:

Opzione A – Broker UNIMORE (usato a laboratorio)
Configuro config.py con le credenziali fornite a lezione:

Opzione B – HiveMQ Cloud (gratuito, niente installazione)
- Registrati su hivemq.com
- Crea un cluster gratuito e copia l'hostname
- Aggiorna conf.py.

## Per la demo d'esame è stato utilizzato il broker UNIMORE del corso. 

---

## ▶️ Avvio del Sistema

### 1. Installazione dipendenze
```bash
pip install -r requirements.txt

python process/data_collector_manager.py

python process/zone_emulator.py




 


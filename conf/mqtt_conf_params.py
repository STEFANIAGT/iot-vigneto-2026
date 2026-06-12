class MqttConfigurationParameters(object):

    BROKER_ADDRESS = "155.185.4.4"
    BROKER_PORT = 7883
    MQTT_USERNAME = "<your_username>"
    MQTT_PASSWORD = "<your_password>"

    # Base topic structure: vigneto/<zone_id>/...
    BASIC_TOPIC = "/iot/user/{0}".format(MQTT_USERNAME)

    # Sub-topics for sensors
    SENSOR_TOPIC = "sensor"
    ENVIRONMENTAL_TOPIC = "environmental"
    IRRIGATION_TOPIC = "irrigation"

    # Sub-topics for device info (retained)
    INFO_TOPIC = "info"

    # Sub-topics for actuator commands
    COMMAND_TOPIC = "command"

    # Data Collector & Manager client id
    DCM_CLIENT_ID = "vigneto-dcm-001"


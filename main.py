import paho.mqtt.client as mqtt
import re
import config
import time
from logger import logger
import os
import GPIOHandler
import gpio4

class MQTTClient:
    open_message_format = re.compile(
        "^(?P<device_id>([0-9]|[a-z]|[A-Z]|[А-Я]|[а-я]|[\_\-\ ])+)/open"
    )
    close_message_format = re.compile(
        "^(?P<device_id>([0-9]|[a-z]|[A-Z]|[А-Я]|[а-я]|[\_\-\ ])+)/close"
    )
    echo_message_format = re.compile(
        "^(?P<device_id>([0-9]|[a-z]|[A-Z]|[А-Я]|[а-я]|[\_\-\ ])+)/echo"
    )
    light_up_request_format = re.compile(
        "^(?P<device_id>([0-9]|[a-z]|[A-Z]|[А-Я]|[а-я]|[\_\-\ ])+)/lightup"
    )
    def __init__(self,
                 device_name: str,
                 username: str,
                 password: str,
                 broker_domain: str,
                 broker_port: int):
        self,
        self.device_name = device_name
        self.username = username
        self.password = password
        self.broker_domain = broker_domain
        self.broker_port = broker_port
        self.subscription_topic = f"{device_name}/#"
        self._connect()

    def _connect(self):
        logger.info(f"USER: {self.username, self.password}, {self.broker_domain, self.broker_port}")
        try:
            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self._client.username_pw_set(self.username, self.password)
            self._client.on_connect = self.on_connect
            self._client.on_disconnect = self.on_disconnect
            self._client.on_message = self.on_message
            self._client.on_log = self.on_log
            self._client.connect(self.broker_domain, self.broker_port, 60)
            self._client.loop_start()
        except Exception as e:
            logger.info("Ошибка в подключении к mqtt")
            self.reconnect_needed = True

    def on_connect(self, client, userdata, flags, rc, properties):
        logger.info(f"Connected with result code {rc}")
        self._client.subscribe(self.subscription_topic)
        self._client.publish(f"{self.device_name}/status/LWT", "Connected")
        os.system(config.COMMAND_ON_LIGHT)

    def on_disconnect(self, client, userdata=None, flags=None, rc=None, properties=None):
        logger.info("Disconnected from broker!!!")
        self._client.publish(f"{self.device_name}/status/LWT", "Connected")
        os.system(config.COMMAND_OFF_BEEPER)
        os.system(config.COMMAND_OFF_LOCK)
        os.system(config.COMMAND_OFF_LIGHT)
        if rc != 0:
            logger.info("Unexpected disconnection.")
            logger.info(client)
            logger.info(userdata)
            logger.info(rc)
        self.reconnect_needed = True

    @staticmethod
    def on_log(client, userdata, paho_log_level, messages):
        logger.info(f"userdata={userdata}")
        logger.info(f"log_level={paho_log_level}")
        logger.info(f"messages={messages}")

    def handle_open_message(self, matched_topic, client, userdata, msg):
        logger.info(f"OPEN: {matched_topic}, {client}, {userdata}, {msg}")
        os.system(config.COMMAND_ON_LOCK)
        os.system(config.COMMAND_ON_BEEPER)
        time.sleep(5)
        os.system(config.COMMAND_OFF_LOCK)
        os.system(config.COMMAND_OFF_BEEPER)

    def handle_close_message(self, matched_topic, client, userdata, msg):
        logger.info(f"CLOSE: {matched_topic}, {client}, {userdata}, {msg}")
        os.system(config.COMMAND_OFF_LOCK)
        os.system(config.COMMAND_OFF_BEEPER)

    def handle_echo_message(self, matched_topic, client, userdata, msg):
        logger.info(f"ECHO: {matched_topic}, {client}, {userdata}, {msg}")

    def handle_light_up_message(self, matched_topic, client, userdata, msg):
        logger.info(f"LIGHTUP: {matched_topic}, {client}, {userdata}, {msg}")
        if int(msg.payload.decode()) == 1:
            os.system(config.COMMAND_ON_LIGHT)
        elif int(msg.payload.decode()) == 0:
            os.system(config.COMMAND_OFF_LIGHT)
        else:
            logger.info("Неизвестное значение в сообщении lightup")

    def run(self):
        while True:
            try:
                self._client.loop_forever(20)
                self._client.publish("SP008/connected", 1)
            except Exception as e:
                logger.opt(exception=e).info("Критическая ошибка в mqtt клиенте:")
            finally:
                if self.reconnect_needed:
                    time.sleep(5)
                    self._connect()
                    self.reconnect_needed = False

    def on_message(self, client, userdata, msg):
        logger.info(f"Пришло сообщение: {client}, {userdata}, {msg}, {msg.topic}, {msg.payload}")
        msg_topic = msg.topic
        if matched_topic := self.open_message_format.match(msg_topic):
            self.handle_open_message(
                matched_topic,
                client,
                userdata,
                msg
            )
        elif matched_topic := self.echo_message_format.match(msg_topic):
            self.handle_echo_message(
                matched_topic,
                client,
                userdata,
                msg
            )
        elif matched_topic := self.close_message_format.match(msg_topic):
            self.handle_close_message(
                matched_topic,
                client,
                userdata,
                msg
            )
        elif matched_topic := self.light_up_request_format.match(msg_topic):
            self.handle_light_up_message(
                matched_topic,
                client,
                userdata,
                msg
            )

    def disconnect(self):
        """Отключение от MQTT брокера"""
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Отключено от MQTT брокера")


def main():
    print(f"{config.DEVICE_NAME}, {config.USERNAME}, {config.PASSWORD}, {config.BROKER_ADDRESS}, {config.PORT}")
    os.system(config.COMMAND_GPIO_ON_BEEPER)
    os.system(config.COMMAND_OFF_BEEPER)
    os.system("gpio readall")
    os.system(config.COMMAND_GPIO_ON_LOCK)
    os.system(config.COMMAND_OFF_LOCK)
    os.system(config.COMMAND_GPIO_ON_LIGHT)
    os.system(config.COMMAND_OFF_LIGHT)
    mqtt_client = MQTTClient(
        config.DEVICE_NAME,
        config.USERNAME,
        config.PASSWORD,
        config.BROKER_ADDRESS,
        config.PORT
    )

    try:
        GPIOHandler.start_monitoring(input_pin=config.GPIO_BUTTON_PIN)
    except Exception as e:
        logger.error(f"Критическая ошибка GPIO: {e}")
    try:
        logger.info("Устройство запущено. Ожидание сообщений...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        GPIOHandler.stop_monitoring()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()

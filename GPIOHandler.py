import config
from logger import logger
import os
import gpio4


class GPIOHandler:
    def __init__(self, pin_number, pin_mode=gpio4.BOARD, pull_up_down=gpio4.PUD_UP):
        self.pin = pin_number
        self.mode = pin_mode
        self.pull = pull_up_down
        self.running = True

        gpio4.GPIO.setmode(self.mode)
        gpio4.GPIO.setup(self.pin, gpio4.IN, pull_up_down=self.pull)
        gpio4.GPIO.add_event_detect(
            self.pin,
            gpio4.BOTH,
            callback=self._pin_change,
            bouncetime=200
        )
        logger.info(f"GPIO: пин {self.pin} настроен (режим {pin_mode})")

    def _pin_change(self, channel):
        state = gpio4.GPIO.input(self.pin)
        logger.info(f"GPIO: пин {channel} изменил состояние на {state}")

        if state == 1:
            self._execute_action()
        else:
            self._execute_stop_action()

    @staticmethod
    def _execute_action(self):
        cmd = config.COMMAND_GPIO_ON_LOCK
        logger.info(f"Выполняется команда: {cmd}")
        os.system(cmd)

    @staticmethod
    def _execute_stop_action(self):
        cmd = config.COMMAND_GPIO_OFF_LOCK
        logger.info(f"Выполняется команда: {cmd}")
        os.system(cmd)

    def stop(self):
        self.running = False
        gpio4.GPIO.remove_event_detect(self.pin)
        gpio4.GPIO.cleanup(self.pin)
        logger.info("GPIO остановлен")

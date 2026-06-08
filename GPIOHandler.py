import threading
import time
import os
import atexit
import config

_monitor_thread = None
_running = False
_pin = None
_last_state = None

def input_callback(state):
    print(f"Пин {_pin} изменился на {state}")
    if state == 0:
        os.system(config.COMMAND_ON_LOCK)
        os.system(config.COMMAND_ON_BEEPER)
    else:
        os.system(config.COMMAND_OFF_LOCK)
        os.system(config.COMMAND_OFF_BEEPER)

def _monitor_loop():
    global _last_state
    os.system(f"gpio mode {_pin} in")

    try:
        result = os.popen(f"gpio read {_pin}").read().strip()
        _last_state = int(result)
    except:
        _last_state = None
        print("Не удалось прочитать начальное состояние пина")

    while _running:
        try:
            result = os.popen(f"gpio read {_pin}").read().strip()
            current_state = int(result)
            if current_state != _last_state:
                _last_state = current_state
                input_callback(current_state)
        except Exception as e:
            print(f"Ошибка в потоке мониторинга: {e}")
        time.sleep(1)

def start_monitoring(input_pin=8):
    global _monitor_thread, _running, _pin
    if _running:
        print("Мониторинг уже запущен")
        return
    _pin = input_pin
    _running = True
    _monitor_thread = threading.Thread(target=_monitor_loop)
    _monitor_thread.daemon = False
    _monitor_thread.start()
    print(f"Мониторинг пина {_pin} запущен в отдельном потоке (опрос 1 сек)")

def stop_monitoring():
    global _running
    _running = False
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=3)
    print("Мониторинг остановлен")

atexit.register(stop_monitoring)
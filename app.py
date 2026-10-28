"""Flask-застосунок з журналюванням і відправкою помилок в імітаційний StatsD."""
import logging
import socket
import threading
import time

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

# --- Журналювання -----------------------------------------------------------
# Логи пишуться у файл app.log і паралельно виводяться в консоль.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# Службові рядки вбудованого сервера (werkzeug) — лише в консоль, щоб app.log був чистим.
_werkzeug = logging.getLogger("werkzeug")
_werkzeug.propagate = False
_werkzeug.addHandler(logging.StreamHandler())

# --- Імітаційний StatsD -----------------------------------------------------
STATSD_HOST = "127.0.0.1"
STATSD_PORT = 8125
_statsd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_statsd(message: str) -> None:
    """Надсилає одне повідомлення по UDP. Якщо сервер недоступний — застосунок не падає."""
    try:
        _statsd_sock.sendto(message.encode("utf-8"), (STATSD_HOST, STATSD_PORT))
    except OSError:
        log.warning("Не вдалося надіслати повідомлення в StatsD")


# --- Застосунок -------------------------------------------------------------
app = Flask(__name__)
app.json.sort_keys = False  # ключі JSON у тому порядку, як записані

START_TIME = time.time()
_lock = threading.Lock()
stats = {"requests": 0, "errors": 0}


@app.before_request
def count_request():
    with _lock:
        stats["requests"] += 1


@app.route("/")
def index():
    log.info("Запит на / — сервіс працює")
    return "Сервіс працює"


@app.route("/error")
def error():
    log.warning("Запит на /error — зараз буде навмисна помилка")
    return 1 / 0  # ZeroDivisionError


@app.route("/status")
def status():
    uptime = round(time.time() - START_TIME, 1)
    log.info("Запит на /status")
    with _lock:
        data = {
            "status": "ok",
            "uptime_seconds": uptime,
            "requests_total": stats["requests"],
            "errors_total": stats["errors"],
        }
    return jsonify(data)


@app.errorhandler(Exception)
def handle_exception(e):
    # HTTP-помилки (наприклад 404) — це не збій коду, тому лише WARNING.
    if isinstance(e, HTTPException):
        log.warning("HTTP %s на %s", e.code, request.path)
        return e

    # Будь-який інший виняток: ERROR з повним traceback + повідомлення в StatsD.
    with _lock:
        stats["errors"] += 1
    log.exception("Виняток на %s", request.path)
    send_statsd(f"flask_app.errors.{type(e).__name__}:1|c")
    return jsonify(error=type(e).__name__, message=str(e)), 500


if __name__ == "__main__":
    log.info("Застосунок запущено на http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000)

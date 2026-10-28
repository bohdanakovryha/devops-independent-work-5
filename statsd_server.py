"""Імітаційний StatsD: UDP-сервер, який приймає повідомлення і виводить їх у консоль."""
import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 8125  # стандартний порт StatsD

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
print(f"Імітаційний StatsD слухає UDP {HOST}:{PORT} (Ctrl+C — зупинити)")

try:
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode("utf-8", errors="replace")
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] від {addr[0]}:{addr[1]} -> {message}")
except KeyboardInterrupt:
    print("\nЗупинено")

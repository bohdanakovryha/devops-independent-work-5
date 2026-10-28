# Flask logging app

A small Flask application with three routes (`/`, `/error`, `/status`) that writes logs to the `app.log` file
in the format `%(asctime)s [%(levelname)s] %(message)s`, and sends a message via UDP
to a mock StatsD server (`statsd_server.py`) for every exception.

To run:

```bash
pip install -r requirements.txt
python statsd_server.py   # terminal 1
python app.py             # terminal 2, application at http://127.0.0.1:5000
```
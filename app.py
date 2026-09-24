import os
import threading
from datetime import datetime

from flask import Flask, render_template, request, send_from_directory

from main import save_places_to_csv, scrape_places

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

app = Flask(__name__)
scrape_lock = threading.Lock()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", queries="", total=10)

    queries_text = request.form.get("queries", "")
    queries = [q.strip() for q in queries_text.splitlines() if q.strip()]
    total = max(1, request.form.get("total", default=10, type=int))
    context = {"queries": queries_text, "total": total}
    if not queries:
        return render_template("index.html", error="Enter at least one search.", **context)
    if not scrape_lock.acquire(blocking=False):
        return render_template("index.html", error="A scrape is already running.", **context)
    try:
        places = scrape_places(queries, total)
    finally:
        scrape_lock.release()

    filename = None
    if places:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
        save_places_to_csv(places, os.path.join(RESULTS_DIR, filename))
    return render_template("index.html", places=places, filename=filename, searched=True, **context)


@app.route("/download/<name>")
def download(name):
    return send_from_directory(RESULTS_DIR, name, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

"""Minimal inference server for the TP53 prediction dashboard (stdlib only).

Serves dashboard/index.html and exposes POST /predict, which runs the real
trained model via scripts/machine_learning/predict.py. No hard-coded results.

Usage: python3 dashboard/server.py [--port 8000]
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "machine_learning"))
from predict import _bundle, predict_variant  # noqa: E402

INDEX = (REPO / "dashboard" / "index.html").read_bytes()
CA_TRACE = (REPO / "dashboard" / "ca_trace.json").read_bytes()
COHORT = (REPO / "results/machine_learning/cohort_summary.json").read_bytes()
FIGS = REPO / "figures" / "machine_learning"
FIG_ALLOW = {"position_enrichment.png", "plddt_by_class.png",
             "substitution_counts.png", "confusion_matrix.png",
             "roc_curve.png", "feature_importance.png",
             "class_distribution.png"}


class Handler(BaseHTTPRequestHandler):
    server_version = "TP53Predictor/1.0"

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(INDEX)))
            self.end_headers()
            self.wfile.write(INDEX)
        elif self.path == "/ca_trace.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(CA_TRACE)))
            self.end_headers()
            self.wfile.write(CA_TRACE)
        elif self.path == "/cohort":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(COHORT)))
            self.end_headers()
            self.wfile.write(COHORT)
        elif self.path.startswith("/fig/") and self.path[5:] in FIG_ALLOW:
            blob = (FIGS / self.path[5:]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)
        else:
            self._send(404, {"error": "Not found."})

    def do_POST(self):
        if self.path != "/predict":
            self._send(404, {"error": "Not found."})
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except (ValueError, OSError):
            self._send(400, {"error": "Invalid request body; send JSON."})
            return
        try:
            self._send(200, predict_variant(data.get("pos"),
                                            data.get("ref"), data.get("alt")))
        except ValueError as e:
            self._send(400, {"error": str(e)})
        except Exception:  # noqa: BLE001 - never leak internals to the UI
            self._send(500, {"error": "Prediction failed due to a server "
                                      "error. Please try again."})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    port = ap.parse_args().port
    _bundle()  # fail fast + warm up before accepting requests
    print("model loaded", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"TP53 Variant Predictor: http://127.0.0.1:{port}  (Ctrl+C to stop)")
    srv.serve_forever()

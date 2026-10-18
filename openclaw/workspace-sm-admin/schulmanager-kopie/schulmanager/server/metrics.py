"""Prometheus-Metriken ohne Zusatzpaket (Text-Exposition-Format 0.0.4)."""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict

PREFIX = "schulmanager"
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)


def _esc(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(pairs: dict[str, str]) -> str:
    if not pairs:
        return ""
    return "{" + ",".join(f'{k}="{_esc(v)}"' for k, v in pairs.items()) + "}"


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        """Setzt alle Zähler zurück (neue App-Instanz)."""
        self.started = time.time()
        self.requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self.hist_counts: dict[tuple[str, str], list[int]] = {}
        self.hist_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.hist_total: dict[tuple[str, str], int] = defaultdict(int)
        self.in_flight = 0
        self.logins: dict[str, int] = defaultdict(int)

    def observe(self, method: str, path: str, status: int, seconds: float) -> None:
        key = (method, path)
        with self._lock:
            self.requests[(method, path, str(status))] += 1
            counts = self.hist_counts.get(key)
            if counts is None:
                counts = self.hist_counts[key] = [0] * len(BUCKETS)
            for i, bound in enumerate(BUCKETS):
                if seconds <= bound:
                    counts[i] += 1
            self.hist_sum[key] += seconds
            self.hist_total[key] += 1

    def login(self, result: str) -> None:
        with self._lock:
            self.logins[result] += 1

    def render(self, gauges: dict[str, tuple[str, list[tuple[dict[str, str], float]]]]) -> str:
        """Erzeugt den Text; ``gauges`` = Name → (Hilfe, [(Labels, Wert)]). Präfix ``schulmanager_``."""
        req, dur = f"{PREFIX}_http_requests_total", f"{PREFIX}_http_request_duration_seconds"
        lines: list[str] = []
        with self._lock:
            lines += [f"# HELP {req} HTTP-Anfragen nach Methode, Routen-Template und Status", f"# TYPE {req} counter"]
            for (m, p, s), n in sorted(self.requests.items()):
                lines.append(f"{req}{_labels({'method': m, 'route': p, 'status': s})} {n}")
            lines += [f"# HELP {dur} Bearbeitungsdauer von HTTP-Anfragen", f"# TYPE {dur} histogram"]
            for (m, p), counts in sorted(self.hist_counts.items()):
                base = {"method": m, "route": p}
                total = self.hist_total[(m, p)]
                for bound, c in zip(BUCKETS, counts):
                    lines.append(f"{dur}_bucket{_labels({**base, 'le': repr(bound)})} {c}")
                lines.append(f"{dur}_bucket{_labels({**base, 'le': '+Inf'})} {total}")
                lines.append(f"{dur}_sum{_labels(base)} {self.hist_sum[(m, p)]:.6f}")
                lines.append(f"{dur}_count{_labels(base)} {total}")
            counters = {
                f"{PREFIX}_logins_total": ("Anmeldeversuche nach Ergebnis",
                                           [({"result": r}, n) for r, n in sorted(self.logins.items())]),
                f"{PREFIX}_login_failures_total": (
                    "Fehlgeschlagene oder gesperrte Anmeldeversuche",
                    [({}, self.logins.get("failure", 0) + self.logins.get("locked", 0))]),
            }
            in_flight = self.in_flight
        for name, (help_text, samples) in counters.items():
            lines += [f"# HELP {name} {help_text}", f"# TYPE {name} counter"]
            lines += [f"{name}{_labels(labels)} {value}" for labels, value in samples]
        gauges = {f"{PREFIX}_http_requests_in_flight": ("Laufende HTTP-Anfragen", [({}, in_flight)]),
                  f"{PREFIX}_uptime_seconds": ("Laufzeit des Prozesses in Sekunden",
                                               [({}, round(time.time() - self.started, 1))]),
                  **gauges}
        for name, (help_text, samples) in gauges.items():
            lines += [f"# HELP {name} {help_text}", f"# TYPE {name} gauge"]
            lines += [f"{name}{_labels(labels)} {value}" for labels, value in samples]
        lines += process_metrics()
        return "\n".join(lines) + "\n"


def process_metrics() -> list[str]:
    """Standard-Prozessmetriken (Linux ``/proc``; auf anderen Systemen soweit verfügbar)."""
    lines: list[str] = []
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        lines += ["# HELP process_cpu_seconds_total Verbrauchte CPU-Zeit (User + System)",
                  "# TYPE process_cpu_seconds_total counter",
                  f"process_cpu_seconds_total {usage.ru_utime + usage.ru_stime:.2f}"]
    except (ImportError, OSError):
        pass
    try:
        with open("/proc/self/statm") as fh:
            pages = int(fh.read().split()[1])
        lines += ["# HELP process_resident_memory_bytes Belegter Arbeitsspeicher (RSS)",
                  "# TYPE process_resident_memory_bytes gauge",
                  f"process_resident_memory_bytes {pages * os.sysconf('SC_PAGE_SIZE')}"]
    except (OSError, ValueError, IndexError, AttributeError):
        pass
    try:
        fds = len(os.listdir("/proc/self/fd"))
        lines += ["# HELP process_open_fds Offene Dateideskriptoren", "# TYPE process_open_fds gauge",
                  f"process_open_fds {fds}"]
    except OSError:
        pass
    return lines


metrics = Metrics()

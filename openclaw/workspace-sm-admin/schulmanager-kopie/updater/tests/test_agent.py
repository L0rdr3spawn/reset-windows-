"""Tests des Update-Agenten: Regeln (``policy``) und Abläufe gegen einen lokalen Lizenzserver mit Test-Schlüsseln
und einer Fake-Laufzeit (kein Docker nötig)."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from lizenzserver import core, updates
from lizenzserver.app import create_app
from lizenzserver.cli import main as lz_main
from updater import policy
from updater.agent import Agent, Config
from updater.client import TransportError, VendorClient
from updater.runtime import FakeRuntime

T0 = datetime(2026, 5, 21, 0, 0, tzinfo=UTC)


# --------------------------------------------------------------------------- policy
def make_manifest(priv, **over):
    m = {"product": "schulpuls", "version": "1.1.0", "channel": "stable", "min_version": "",
         "migration": {"present": False, "backward_compatible": True}, "notes": "",
         "dist": {"type": "download", "file": "schulpuls-1.1.0.tar", "sha256": "a" * 64, "size": 10}}
    m.update(over)
    sig = base64.b64encode(priv.sign(policy.canonical(m))).decode()
    return m, sig


def test_check_release_rules():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    m, sig = make_manifest(priv)
    assert policy.check_release(m, sig, pub, installed="1.0.0").ok
    assert not policy.check_release(m, sig, Ed25519PrivateKey.generate().public_key(), installed="1.0.0").ok   # fremder Schlüssel
    tampered = {**m, "version": "9.9.9"}
    assert not policy.check_release(tampered, sig, pub, installed="1.0.0").ok                                 # Manifest verändert
    assert not policy.check_release(m, "", pub, installed="1.0.0").ok
    v = policy.check_release(m, sig, pub, installed="1.1.0")
    assert not v.ok and "Downgrade" in v.reason
    v = policy.check_release(m, sig, pub, installed="1.0.0", highest_installed="1.3.0")
    assert not v.ok and "Downgrade" in v.reason
    m2, s2 = make_manifest(priv, min_version="1.0.5")
    assert "Mindestversion" in policy.check_release(m2, s2, pub, installed="1.0.0").reason
    m3, s3 = make_manifest(priv, dist={"type": "registry", "image": "evil.example/x", "digest": "sha256:" + "b" * 64})
    assert policy.check_release(m3, s3, pub, installed="1.0.0").ok
    assert not policy.check_release(m3, s3, pub, installed="1.0.0", allowed_registry="registry.anbieter.de/").ok
    m4, s4 = make_manifest(priv, dist={"type": "registry", "image": "reg/x", "digest": "latest"})
    assert not policy.check_release(m4, s4, pub, installed="1.0.0").ok
    m5, s5 = make_manifest(priv, dist={"type": "shell", "cmd": "rm -rf /"})
    assert not policy.check_release(m5, s5, pub, installed="1.0.0").ok          # nur bekannte Verteilungsarten
    m6, s6 = make_manifest(priv, product="anderes")
    assert not policy.check_release(m6, s6, pub, installed="1.0.0").ok


def test_rollback_decisions():
    f = policy.after_image_rollback
    assert policy.after_update(True) == "keep" and policy.after_update(False) == "rollback"
    assert f(old_healthy=True, migration_present=False, backward_compatible=True, allow_db_restore=True, has_backup=True) == "done"
    assert f(old_healthy=True, migration_present=True, backward_compatible=True, allow_db_restore=True, has_backup=True) == "done"
    assert f(old_healthy=True, migration_present=True, backward_compatible=False, allow_db_restore=True, has_backup=True) == "restore_db"
    assert f(old_healthy=False, migration_present=False, backward_compatible=True, allow_db_restore=True, has_backup=True) == "restore_db"
    # andere Server nutzen dieselbe Datenbank: nie einspielen
    assert f(old_healthy=False, migration_present=True, backward_compatible=True, allow_db_restore=False, has_backup=True) == "give_up"
    assert f(old_healthy=True, migration_present=True, backward_compatible=False, allow_db_restore=False, has_backup=True) == "give_up"
    assert f(old_healthy=False, migration_present=False, backward_compatible=True, allow_db_restore=True, has_backup=False) == "give_up"


# --------------------------------------------------------------------------- Simulation
class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def add(self, **kw):
        self.t += timedelta(**kw)


class TcTransport:
    """Spricht den Lizenzserver in-process an (wie HTTP, ohne Port)."""

    def __init__(self, client: TestClient):
        self.c = client
        self.tamper = False
        self.bad_signature = False

    @staticmethod
    def _path(url):
        return "/" + url.split("//", 1)[1].split("/", 1)[1]

    def post_json(self, url, body, timeout):
        r = self.c.post(self._path(url), json=body)
        if r.status_code != 200:
            raise TransportError(f"HTTP {r.status_code}")
        data = r.json()
        if self.bad_signature:
            data["signature"] = base64.b64encode(b"x" * 64).decode()
        return data

    def download(self, url, headers, dest, timeout):
        r = self.c.get(self._path(url), headers=headers)
        if r.status_code != 200:
            raise TransportError(f"HTTP {r.status_code}")
        content = r.content + (b"!" if self.tamper else b"")
        dest.write_bytes(content)
        return hashlib.sha256(content).hexdigest(), len(content)


@pytest.fixture
def world(tmp_path, monkeypatch, capsys):
    lz = tmp_path / "lz"
    lz.mkdir()
    monkeypatch.setenv("LZ_DATA_DIR", str(lz))
    monkeypatch.setenv("LZ_RELEASE_DIR", str(lz / "rel"))
    monkeypatch.delenv("LZ_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("LZ_ADMIN_PASSWORD_HASH", raising=False)
    assert lz_main(["keygen"]) == 0
    pubkey = capsys.readouterr().out.splitlines()[0]
    clock = Clock(T0)
    monkeypatch.setattr(updates, "now", clock)
    engine = core.make_engine()
    updates.init(engine)
    client = TestClient(create_app())
    transport = TcTransport(client)

    class World:
        pass

    w = World()
    w.tmp, w.pubkey, w.clock, w.client, w.transport, w.engine = tmp_path, pubkey, clock, client, transport, engine
    w.agents = {}

    def school(name="Schule", servers=1):
        out = []
        with Session(engine) as s:
            sc = core.create_school(s, name=name, servers=servers)
            for i in range(servers):
                k, text = core.issue_key(s, sc, label=f"Server {i + 1}")
                core.bind(k, f"inst-{name}-{i}", f"https://{i}.example")
                out.append((k.id, text, f"inst-{name}-{i}"))
            s.commit()
        return out

    def release(version="1.1.0", **kw):
        updates.release_dir().joinpath(f"schulpuls-{version}.tar").write_bytes(b"IMG-" + version.encode())
        with Session(engine) as s:
            r = updates.create_release(s, core.load_key(), version=version, file=f"schulpuls-{version}.tar", **kw)
            s.commit()
            return r.id

    def rollout(rid, **kw):
        kw.setdefault("test_first", False)
        kw.setdefault("wave_percent", 100)
        kw.setdefault("urgent", True)
        with Session(engine) as s:
            ro = updates.create_rollout(s, name="R", release_id=rid, **kw)
            updates.set_rollout_status(s, ro, "active")
            ro.started_at = datetime(2020, 1, 1, tzinfo=UTC)
            s.commit()
            return ro.id

    def agent(server, node="main", rt=None, **cfg):
        key_id, text, inst = server
        data = tmp_path / f"data-{key_id}"
        (data).mkdir(exist_ok=True)
        (data / "license.json").write_text(json.dumps({"key": text}))
        (data / "license_state.json").write_text(json.dumps({"instance_id": inst}))
        rt = rt or FakeRuntime()
        c = Config(vendor_url="https://lizenz.test", pubkey=pubkey, data_dir=data, state_dir=tmp_path / f"state-{key_id}",
                   node=node, drain_seconds=0, health_timeout=30, health_interval=1, **cfg)
        a = Agent(c, VendorClient(c.vendor_url, transport), rt, clock=clock, sleep=lambda s: clock.add(seconds=s))
        w.agents[key_id] = a
        return a

    w.school, w.release, w.rollout, w.agent = school, release, rollout, agent
    return w


def status(agent):
    return json.loads((agent.cfg.data_dir / "updater" / "status.json").read_text(encoding="utf-8"))


def test_happy_path_single_server(world):
    srv = world.school()[0]
    world.rollout(world.release())
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    step = a.tick()
    assert step.action == "install" and a.st["state"] == "healthy"
    assert rt.image == "schulpuls-app:1.1.0" and rt.calls.index("backup") < rt.calls.index("apply_image")
    assert a.st["highest"] == "1.1.0" and a.st["in_progress"] is None
    assert not (a.cfg.data_dir / f"drain-{a.node_id}.flag").exists()           # wieder im Lastausgleich
    assert status(a)["version"] == "1.1.0" and status(a)["state"] == "healthy"
    assert world.agents[srv[0]].tick().action == "none"                          # danach: nichts mehr zu tun
    with Session(world.engine) as s:
        n = s.query(updates.Node).filter_by(key_id=srv[0]).one()
        assert n.version == "1.1.0"
        states = [e.state for e in s.query(updates.UpdateEvent).filter_by(key_id=srv[0], kind="node")]
    for expected in ("downloading", "draining", "backing_up", "updating", "verifying", "healthy"):
        assert expected in states                                                # Protokoll beim Anbieter


def test_drain_flag_is_set_during_install(world):
    srv = world.school()[0]
    world.rollout(world.release())
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    seen = []
    orig = rt.apply_image
    rt.apply_image = lambda ref: (seen.append((a.cfg.data_dir / f"drain-{a.node_id}.flag").exists()), orig(ref))[1]
    a.tick()
    assert seen == [True]


def test_unhealthy_new_version_rolls_back_and_stays_failed_until_retry(world):
    srv = world.school()[0]
    world.rollout(world.release())
    rt = FakeRuntime(images={"schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False}})
    a = world.agent(srv, rt=rt)
    a.tick()
    assert a.st["state"] == "rolled_back" and rt.image == "schulpuls-app:1.0.0"
    assert "restore" not in rt.calls                                             # keine Migration: Sicherung bleibt liegen
    assert "1.1.0" in a.st["failed"] and a.st["highest"] == ""
    assert not (a.cfg.data_dir / f"drain-{a.node_id}.flag").exists()
    a.tick()
    assert rt.calls.count("apply_image") == 2                                    # nur Update + Rollback, kein neuer Versuch
    # Anbieter drückt „Erneut versuchen“, Version ist inzwischen repariert
    with Session(world.engine) as s:
        updates.retry_node(s, srv[0])
        s.commit()
    rt.images["schulpuls-app:1.1.0"] = {"version": "1.1.0", "healthy": True}
    a.tick()                                                                     # lernt retry_seq
    a.tick()
    assert a.st["state"] == "healthy" and rt.image == "schulpuls-app:1.1.0"


def test_incompatible_migration_failure_restores_database(world):
    srv = world.school()[0]
    world.rollout(world.release(has_migration=True, backward_compatible=False))
    rt = FakeRuntime(images={
        "schulpuls-app:1.0.0": {"version": "1.0.0", "works_with": ["1.0.0"]},
        "schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False, "migrates_to": "1.1.0"}})
    a = world.agent(srv, rt=rt)
    a.tick()
    assert rt.schema == "1.0.0"                                                  # Datenbank aus der Sicherung
    assert "restore" in rt.calls and rt.image == "schulpuls-app:1.0.0"
    assert a.st["state"] == "rolled_back" and "Sicherung eingespielt" in a.st["detail"]


def test_compatible_migration_failure_only_swaps_image(world):
    srv = world.school()[0]
    world.rollout(world.release(has_migration=True, backward_compatible=True))
    rt = FakeRuntime(images={
        "schulpuls-app:1.0.0": {"version": "1.0.0", "works_with": ["1.0.0", "1.1.0"]},
        "schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False, "migrates_to": "1.1.0"}})
    a = world.agent(srv, rt=rt)
    a.tick()
    assert "restore" not in rt.calls and rt.schema == "1.1.0"                    # altes Image läuft auf neuem Schema
    assert a.st["state"] == "rolled_back" and rt.image == "schulpuls-app:1.0.0"


def test_old_image_cannot_run_on_new_schema_escalates_to_restore(world):
    srv = world.school()[0]
    world.rollout(world.release(has_migration=True, backward_compatible=True))     # Anbieter hat sich geirrt
    rt = FakeRuntime(images={
        "schulpuls-app:1.0.0": {"version": "1.0.0", "works_with": ["1.0.0"]},
        "schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False, "migrates_to": "1.1.0"}})
    a = world.agent(srv, rt=rt)
    a.tick()
    assert "restore" in rt.calls and rt.schema == "1.0.0" and a.st["state"] == "rolled_back"


def test_backup_failure_means_no_update(world):
    srv = world.school()[0]
    world.rollout(world.release())
    rt = FakeRuntime(fail_on={"backup"})
    a = world.agent(srv, rt=rt)
    a.tick()
    assert "apply_image" not in rt.calls and rt.image == "schulpuls-app:1.0.0"
    assert a.st["state"] in ("rolled_back", "error") and "Sicherung" in a.st["detail"]
    assert not (a.cfg.data_dir / f"drain-{a.node_id}.flag").exists()


def test_tampered_download_is_rejected(world):
    srv = world.school()[0]
    world.rollout(world.release())
    world.transport.tamper = True
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    a.tick()
    assert "load_image" not in rt.calls and "apply_image" not in rt.calls
    assert "Prüfsumme" in a.st["detail"] or "Prüfsumme" in json.dumps(a.st["log"])
    assert not list((a.cfg.state_dir / "downloads").glob("*.tar"))               # nichts bleibt liegen


def test_unsigned_vendor_answer_is_ignored(world):
    srv = world.school()[0]
    world.rollout(world.release())
    world.transport.bad_signature = True
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    step = a.tick()
    assert step.action == "none" and "apply_image" not in rt.calls and "signiert" in a.last_error


def test_wrong_pinned_key_is_refused(world):
    srv = world.school()[0]
    world.rollout(world.release())
    a = world.agent(srv)
    a.tick()
    other = base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()).decode()
    cfg = Config(vendor_url=a.cfg.vendor_url, pubkey=other, data_dir=a.cfg.data_dir, state_dir=a.cfg.state_dir)
    with pytest.raises(SystemExit):
        Agent(cfg, a.client, FakeRuntime())                                       # Schlüssel-Pinning


def test_downgrade_protection_in_agent(world):
    srv = world.school()[0]
    world.rollout(world.release("1.1.0"))
    a = world.agent(srv)
    a.st["highest"] = "1.2.0"                                                     # früher schon 1.2.0 gehabt
    a._save()
    step = a.tick()
    assert step.action == "none" and "Downgrade" in step.detail


def test_postpone_once_max_days_and_never_when_urgent(world):
    srv = world.school()[0]
    world.rollout(world.release(), urgent=False, start_at=T0 - timedelta(hours=1), run_hours=1000)
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    plan = a.cfg.data_dir / "updater" / "plan.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    a.tick()                                                                      # Angebot kennenlernen (installiert, da offen) …
    # … deshalb Neustart-frisch: gleicher Test mit Verschieben vor dem ersten Tick
    srv2 = world.school("Zwei")[0]
    a2 = world.agent(srv2, rt=FakeRuntime())
    plan2 = a2.cfg.data_dir / "updater" / "plan.json"
    plan2.parent.mkdir(parents=True, exist_ok=True)
    a2.offered = {"version": "1.1.0"}                                             # Administration sieht das Angebot in /betrieb
    plan2.write_text(json.dumps({"postpone": {"version": "1.1.0", "until": (T0 + timedelta(days=30)).isoformat()}}))
    step = a2.tick()
    assert step.action == "prepare" and a2.st["state"] == "postponed" and "apply_image" not in a2.rt.calls
    until = datetime.fromisoformat(a2.st["postponed"]["1.1.0"].replace("Z", "+00:00"))
    assert until <= T0 + timedelta(days=7, seconds=5)                              # höchstens 7 Tage
    plan2.write_text(json.dumps({"postpone": {"version": "1.1.0", "until": (T0 + timedelta(days=2)).isoformat()}}))
    a2.tick()
    assert a2.st["postponed"]["1.1.0"] == _iso(until)                              # nur einmal je Version
    world.clock.add(days=8)
    a2.tick()
    assert a2.st["state"] == "healthy"                                             # danach geht es los


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_urgent_ignores_postponement(world):
    srv = world.school()[0]
    world.rollout(world.release(), urgent=True)
    a = world.agent(srv)
    plan = a.cfg.data_dir / "updater" / "plan.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    a.offered = {"version": "1.1.0"}
    plan.write_text(json.dumps({"postpone": {"version": "1.1.0", "until": (T0 + timedelta(days=3)).isoformat()}}))
    a.tick()
    assert a.st["state"] == "healthy"


def test_manual_mode_installs_only_on_request(world):
    srv = world.school()[0]
    world.rollout(world.release(), urgent=False, start_at=T0 - timedelta(hours=1))
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt, mode="manual")
    step = a.tick()
    assert step.action == "none" or step.state == "manual"
    assert a.st["state"] == "manual" and "apply_image" not in rt.calls
    assert status(a)["offered"]["version"] == "1.1.0" and status(a)["mode"] == "manual"
    plan = a.cfg.data_dir / "updater" / "plan.json"
    plan.write_text(json.dumps({"install_now": {"id": "r1", "version": "1.1.0"}}))
    a.tick()
    assert a.st["state"] == "healthy" and rt.image == "schulpuls-app:1.1.0"
    a.tick()
    assert rt.calls.count("apply_image") == 1                                      # Auftrag wird nur einmal ausgeführt


def test_crash_recovery_finishes_or_rolls_back(world):
    srv = world.school()[0]
    world.rollout(world.release())
    rt = FakeRuntime(image="schulpuls-app:1.1.0", images={"schulpuls-app:1.1.0": {"version": "1.1.0"}})
    a = world.agent(srv, rt=rt)
    a.st["in_progress"] = {"version": "1.1.0", "prev_image": "schulpuls-app:1.0.0", "ref": "schulpuls-app:1.1.0",
                           "backup": "b1", "migration": {"present": False, "backward_compatible": True},
                           "allow_restore": True}
    a._save()
    a2 = Agent(a.cfg, a.client, rt, clock=world.clock, sleep=lambda s: world.clock.add(seconds=s))
    a2.tick()
    assert a2.st["highest"] == "1.1.0" and a2.st["state"] == "healthy"          # lief schon: zu Ende geführt
    # Variante: neue Version ist kaputt
    rt2 = FakeRuntime(image="schulpuls-app:1.1.0",
                      images={"schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False},
                              "schulpuls-app:1.0.0": {"version": "1.0.0"}})
    srv2 = world.school("Eins")[0]
    world.rollout(world.release("1.2.0"))
    b = world.agent(srv2, rt=rt2)
    b.st["in_progress"] = {"version": "1.1.0", "prev_image": "schulpuls-app:1.0.0", "ref": "schulpuls-app:1.1.0",
                           "backup": None, "migration": {"present": False, "backward_compatible": True},
                           "allow_restore": True}
    b.st["in_progress"]["prev_version"] = "1.0.0"
    b._save()
    b.recover(("k", "i"), "1.1.0")
    assert rt2.image == "schulpuls-app:1.0.0" and b.st["state"] == "rolled_back"


def test_window_with_appointment_end_to_end(world):
    srv = world.school()[0]
    world.rollout(world.release(), urgent=False, start_at=T0 + timedelta(hours=2))
    rt = FakeRuntime()
    a = world.agent(srv, rt=rt)
    step = a.tick()
    assert step.action == "prepare" and a.st["state"] == "ready" and "apply_image" not in rt.calls
    assert status(a)["prepared"] == "1.1.0" and status(a)["window"]["inside"] is False
    world.clock.add(hours=2, minutes=1)
    a.tick()
    assert a.st["state"] == "healthy"


def test_two_servers_rolling_update_never_both_down(world):
    srvs = world.school("Zwei", servers=2)
    world.rollout(world.release())
    rts = [FakeRuntime(), FakeRuntime()]
    agents = [world.agent(srvs[i], node=f"n{i}", rt=rts[i]) for i in range(2)]
    # beide Server kennen sich beim Anbieter
    for a in agents:
        a._ask(a._identity(), "1.0.0", {})
    both_busy = []
    online_counts = []
    orig = [rt.apply_image for rt in rts]

    def wrap(i):
        def f(ref):
            others_up = rts[1 - i].running and not (agents[1 - i].cfg.data_dir / f"drain-{agents[1 - i].node_id}.flag").exists()
            online_counts.append(others_up)
            return orig[i](ref)
        return f
    for i in range(2):
        rts[i].apply_image = wrap(i)
    for _ in range(3):
        for a in agents:
            a.tick()
            world.clock.add(minutes=2)
    assert [a.st["state"] for a in agents] == ["healthy", "healthy"]
    assert all(online_counts) and len(online_counts) == 2                          # der jeweils andere war online
    assert not both_busy
    with Session(world.engine) as s:
        evs = [(e.key_id, e.state) for e in s.query(updates.UpdateEvent).filter(updates.UpdateEvent.state.in_(("draining", "healthy"))).order_by(updates.UpdateEvent.id)]
    first, second = srvs[0][0], srvs[1][0]
    seq = [e for e in evs if e[1] in ("draining", "healthy")]
    assert seq.index((first, "healthy")) < seq.index((second, "draining"))         # erst gesund, dann der nächste


def test_two_servers_failure_halts_second(world):
    srvs = world.school("Zwei", servers=2)
    world.rollout(world.release())
    rts = [FakeRuntime(images={"schulpuls-app:1.1.0": {"version": "1.1.0", "healthy": False}}), FakeRuntime()]
    agents = [world.agent(srvs[i], node=f"n{i}", rt=rts[i]) for i in range(2)]
    for a in agents:
        a._ask(a._identity(), "1.0.0", {})
    for _ in range(3):
        for a in agents:
            a.tick()
            world.clock.add(minutes=2)
    assert agents[0].st["state"] == "rolled_back"
    assert "apply_image" not in rts[1].calls and agents[1].st["state"] != "healthy"   # zweiter Server bleibt unberührt


def test_maintenance_window_three_servers_incompatible_migration(world):
    srvs = world.school("Drei", servers=3)
    world.rollout(world.release(has_migration=True, backward_compatible=False))
    rts = [FakeRuntime() for _ in range(3)]
    agents = [world.agent(srvs[i], node=f"n{i}", rt=rts[i]) for i in range(3)]
    for a in agents:
        a._ask(a._identity(), "1.0.0", {})
    # Vorbereiten
    for a in agents:
        a.tick()
        world.clock.add(minutes=1)
    for _ in range(6):
        for a in agents:
            a.tick()
            world.clock.add(minutes=1)
    assert [a.st["state"] for a in agents] == ["healthy"] * 3
    assert all(rt.image == "schulpuls-app:1.1.0" for rt in rts)
    # die Folger wurden vor der Migration des ersten Servers angehalten
    assert "stop_app" in rts[1].calls and "stop_app" in rts[2].calls and "stop_app" not in rts[0].calls


def test_no_license_no_action(world):
    srv = world.school()[0]
    a = world.agent(srv)
    (a.cfg.data_dir / "license.json").unlink()
    assert a.tick().detail == "Keine Lizenz"

#!/usr/bin/env python3
"""Seed the simplified "Nordic Test Lab" demo into SINDIT through its REST API.

Three nodes, chosen to show three things:

* Climate Testing Service  - a service offer (static properties)
* Climate Chamber CC-01    - equipment with a datasheet in MinIO (S3 connection) and
                             live temperature + status over MQTT
* Test Report TC-2026-014  - an internal record that is NOT shared via the dataspace

Links: Service --uses--> Chamber, Report --derivedFrom--> Service.

Only the Python standard library is used. Re-running is safe: every node has a
deterministic URI, and SINDIT's create endpoints replace an existing node.

Usage:
    python demo/seed_nordic_test_lab.py --api https://sindit2-api.sintef.cloud \
        --username <user> --workspace NordicTestLab \
        [--s3-connection <uri> --s3-bucket sindit-demo --s3-key <key>]
    python demo/seed_nordic_test_lab.py ... --reset   # delete the demo nodes again

The password is prompted for if not given (or set SINDIT_PASSWORD).
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

XSD = "http://www.w3.org/2001/XMLSchema#"
QUDT = "http://qudt.org/vocab/unit/"

DEFAULT_MQTT_HOST = "sindit-2-demo-mqtt.sindit.svc.cluster.local"
CLIMATE_TOPIC = "nordic-test-lab/cc01/climate"
STATUS_TOPIC = "nordic-test-lab/cc01/status"

# Static properties: (slug, name, value, xsd type, QUDT unit or None)
SERVICE_PROPS = [
    ("standards", "Applicable standards", "IEC 60068-2-1, -2-2, -2-78", "string", None),
    ("lead-time", "Typical lead time (weeks)", 2, "integer", None),
]
CHAMBER_PROPS = [
    ("temp-range", "Temperature range", "-70 to +180 °C", "string", None),
]
REPORT_PROPS = [
    ("result", "Result", "Pass", "string", None),
    ("max-deviation", "Max temperature deviation", 0.4, "float", "DEG_C"),
]

# Live MQTT properties on the chamber: (slug, name, topic, JSON field, xsd, unit)
CHAMBER_STREAMS = [
    (
        "live-temperature",
        "Chamber temperature (live)",
        CLIMATE_TOPIC,
        "temperature",
        "float",
        "DEG_C",
    ),
    ("live-status", "Chamber status (live)", STATUS_TOPIC, "status", "string", None),
]

ASSETS = {
    # slug: (label, assetType, description)
    "svc-climate-testing": (
        "Climate Testing Service",
        "Service",
        "Temperature and humidity testing of components and products.",
    ),
    "climate-chamber-cc01": (
        "Climate Chamber CC-01",
        "Equipment",
        "Walk-in climate chamber. Datasheet in MinIO, live readings over MQTT.",
    ),
    "test-report-tc-2026-014": (
        "Test Report TC-2026-014",
        "Test record",
        "Completed customer test. Internal - not shared via the dataspace.",
    ),
}

RELATIONSHIPS = [
    (
        "uses",
        "svc-climate-testing",
        "climate-chamber-cc01",
        "Service is performed with",
    ),
    (
        "derivedFrom",
        "test-report-tc-2026-014",
        "svc-climate-testing",
        "Report delivered under",
    ),
]

# Nodes to publish to the dataspace in the demo (the report stays internal).
PUBLISH_SUGGESTION = ["svc-climate-testing", "climate-chamber-cc01"]


# ----------------------------------------------------------------- HTTP helpers
class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.token: str | None = None

    def _call(self, method, path, *, params=None, body=None, form=None):
        url = f"{self.base}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {detail}") from None

    def login(self, username, password):
        res = self._call(
            "POST", "/token", form={"username": username, "password": password}
        )
        self.token = res["access_token"]

    def get(self, path, **params):
        return self._call("GET", path, params=params or None)

    def post(self, path, body=None, **params):
        return self._call("POST", path, params=params or None, body=body)

    def delete(self, path, **params):
        return self._call("DELETE", path, params=params or None)


def uri_prefix_from_workspace(ws_uri: str) -> str:
    """Same rule as the frontend's create-node modal: up to the last '#' or '/'."""
    idx = max(ws_uri.rfind("#"), ws_uri.rfind("/"))
    return ws_uri[: idx + 1] if idx >= 0 else ws_uri + "#"


# ----------------------------------------------------------------- seeding
def static_prop(uri, name, value, xsd_type, unit):
    payload = {
        "uri": uri,
        "label": name,
        "propertyName": name,
        "propertyValue": value,
        "propertyDataType": {"uri": XSD + xsd_type},
    }
    if unit:
        payload["propertyUnit"] = {"uri": QUDT + unit}
    return payload


def wait_connected(api: Api, uri: str, timeout: int = 60) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        node = api.get("/kg/node", node_uri=uri, depth=1) or {}
        if str(node.get("isConnected")).lower() == "true":
            return True
        time.sleep(3)
    return False


def seed(api: Api, prefix: str, args) -> None:
    def u(slug: str) -> str:
        return f"{prefix}ntl-{slug}"

    # MQTT connection (cluster-internal broker; SINDIT and the simulator use it)
    mqtt_uri = u("demo-mqtt")
    api.post(
        "/kg/connection",
        {
            "uri": mqtt_uri,
            "label": "Demo MQTT broker",
            "type": "MQTT",
            "host": args.mqtt_host,
            "port": args.mqtt_port,
            "connectionDescription": "Demo broker with simulated climate-chamber data",
        },
    )
    ok = wait_connected(api, mqtt_uri)
    print(
        f"  conn   Demo MQTT broker ({args.mqtt_host}:{args.mqtt_port})"
        f" connected={ok}"
    )

    prop_refs: dict[str, list[dict]] = {}

    def add_static(asset_slug, props):
        refs = prop_refs.setdefault(asset_slug, [])
        for slug, name, value, xsd_type, unit in props:
            uri = u(f"{asset_slug}-{slug}")
            api.post(
                "/kg/asset_property", static_prop(uri, name, value, xsd_type, unit)
            )
            refs.append({"uri": uri})

    add_static("svc-climate-testing", SERVICE_PROPS)
    add_static("climate-chamber-cc01", CHAMBER_PROPS)
    add_static("test-report-tc-2026-014", REPORT_PROPS)

    # Live MQTT properties on the chamber
    for slug, name, topic, field, xsd_type, unit in CHAMBER_STREAMS:
        uri = u(f"climate-chamber-cc01-{slug}")
        payload = {
            "uri": uri,
            "label": name,
            "propertyName": name,
            "propertyDataType": {"uri": XSD + xsd_type},
            "propertyConnection": {"uri": mqtt_uri},
            "streamingTopic": topic,
            "streamingPath": field,
        }
        if unit:
            payload["propertyUnit"] = {"uri": QUDT + unit}
        api.post("/kg/streaming_property", payload)
        prop_refs["climate-chamber-cc01"].append({"uri": uri})
        print(f"  mqtt   {name}: topic {topic}, field '{field}'")

    # Datasheet in MinIO through an existing S3 connection (optional)
    if args.s3_connection:
        uri = u("climate-chamber-cc01-datasheet-pdf")
        try:
            exists = bool(api.get("/kg/node", node_uri=uri, depth=0))
        except RuntimeError:
            exists = False
        if exists:
            # Never re-save an existing S3 property: SINDIT's re-save detaches the
            # old property, and its cleanup DELETES the file from the bucket.
            prop_refs["climate-chamber-cc01"].append({"uri": uri})
            print(f"  s3     Datasheet (PDF): kept existing property ({uri})")
            args.s3_connection = None
    if args.s3_connection:
        api.post(
            "/kg/s3_object",
            {
                "uri": uri,
                "label": "Datasheet (PDF)",
                "propertyName": "Datasheet (PDF)",
                "propertyDescription": "Equipment datasheet stored in MinIO",
                "propertyConnection": {"uri": args.s3_connection},
                "bucket": args.s3_bucket,
                "key": args.s3_key,
            },
        )
        prop_refs["climate-chamber-cc01"].append({"uri": uri})
        print(f"  s3     Datasheet (PDF): {args.s3_bucket}/{args.s3_key}")

    for slug, (label, asset_type, description) in ASSETS.items():
        api.post(
            "/kg/asset",
            {
                "uri": u(slug),
                "label": label,
                "assetType": asset_type,
                "assetDescription": description,
                "assetProperties": prop_refs.get(slug, []),
            },
        )
        print(
            f"  asset  {label:<26} ({asset_type}, "
            f"{len(prop_refs.get(slug, []))} properties)"
        )

    for rel_type, src, tgt, desc in RELATIONSHIPS:
        api.post(
            "/kg/relationship",
            {
                "uri": u(f"rel-{rel_type}-{src}-{tgt}"),
                "relationshipType": rel_type,
                "relationshipDescription": desc,
                "relationshipSource": {"uri": u(src)},
                "relationshipTarget": {"uri": u(tgt)},
            },
        )
        print(f"  link   {ASSETS[src][0]} --{rel_type}--> {ASSETS[tgt][0]}")

    print("\nPublish these to the dataspace in the demo (the report stays internal):")
    for slug in PUBLISH_SUGGESTION:
        print(f"  {u(slug)}")


def all_uris(prefix: str, include_s3: bool) -> list[str]:
    def u(slug: str) -> str:
        return f"{prefix}ntl-{slug}"

    uris = [u(f"rel-{t}-{s}-{g}") for t, s, g, _ in RELATIONSHIPS]
    uris += [u(f"svc-climate-testing-{p[0]}") for p in SERVICE_PROPS]
    uris += [u(f"climate-chamber-cc01-{p[0]}") for p in CHAMBER_PROPS + CHAMBER_STREAMS]
    uris += [u(f"test-report-tc-2026-014-{p[0]}") for p in REPORT_PROPS]
    if include_s3:
        uris.append(u("climate-chamber-cc01-datasheet-pdf"))
    uris += [u(slug) for slug in ASSETS]
    uris.append(u("demo-mqtt"))
    return uris


def reset(api: Api, prefix: str, args) -> None:
    uris = all_uris(prefix, include_s3=bool(args.s3_connection))
    for uri in uris:
        try:
            api.delete("/kg/node", node_uri=uri)
        except RuntimeError as e:
            print(f"  skip {uri}: {e}")
    print(f"Deleted up to {len(uris)} demo nodes (files in MinIO are not touched).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--api", default=os.environ.get("SINDIT_API", "http://localhost:9017")
    )
    ap.add_argument("--username", default=os.environ.get("SINDIT_USERNAME"))
    ap.add_argument("--password", default=os.environ.get("SINDIT_PASSWORD"))
    ap.add_argument("--workspace", default="NordicTestLab")
    ap.add_argument("--mqtt-host", default=DEFAULT_MQTT_HOST)
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument(
        "--s3-connection", help="URI of an existing S3 connection in SINDIT"
    )
    ap.add_argument("--s3-bucket", default="sindit-demo")
    ap.add_argument("--s3-key", default="nordic-test-lab/datasheets/CC01-datasheet.pdf")
    ap.add_argument(
        "--reset", action="store_true", help="Delete the demo nodes instead"
    )
    args = ap.parse_args()

    if not args.username:
        ap.error("--username (or SINDIT_USERNAME) is required")
    password = args.password or getpass.getpass(
        f"SINDIT password for {args.username}: "
    )

    api = Api(args.api)
    api.login(args.username, password)
    ws = api.post("/ws/switch", workspace_name=args.workspace)
    ws_uri = (ws or {}).get("uri") or api.get("/ws/get")["uri"]
    prefix = uri_prefix_from_workspace(ws_uri)
    print(f"Workspace: {ws_uri}\nNode URI prefix: {prefix}ntl-\n")

    (reset if args.reset else seed)(api, prefix, args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

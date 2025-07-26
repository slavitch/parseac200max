#!/usr/bin/env python3
import sys
import json
import base64


def parse_multiline_json(stream):
    """
    Generator that yields full JSON objects from a stream, even if spanning multiple lines.
    """
    buf = ""
    depth = 0
    in_str = False
    escape = False

    while True:
        ch = stream.read(1)
        if not ch:
            break
        buf += ch

        if ch == '"' and not escape:
            in_str = not in_str
        if in_str and ch == '\\' and not escape:
            escape = True
            continue
        if escape:
            escape = False

        if not in_str:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1

        if depth == 0 and buf.strip():
            try:
                yield json.loads(buf)
            except json.JSONDecodeError:
                pass
            buf = ""


def main():
    """
    Read multi-line Bluetti JSON records from stdin, but only process those
    with command "AQMARgBCJC4=", decode their payloads, and output parsed JSON
    with:
      - timestamp
      - type
      - command
      - soc_pct
      - pv_watts_in
      - ac_watts_out
      - dc_watts_out
    """
    for rec in parse_multiline_json(sys.stdin):
        if rec.get("command") != "AQMARgBCJC4=":
            continue

        payload = rec.get("data", "") or rec.get("command", "")
        try:
            raw = base64.b64decode(payload)
        except Exception:
            continue

        if len(raw) < 0x35:
            continue

        ts  = rec.get("time") or rec.get("timestamp")
        soc = raw[0x34]
        pv  = int.from_bytes(raw[0x28:0x2A], byteorder="little", signed=False)
        ac  = int.from_bytes(raw[0x30:0x32], byteorder="little", signed=False)
        dc  = int.from_bytes(raw[0x32:0x34], byteorder="little", signed=False)

        out = {
            "timestamp":    ts,
            "type":         rec.get("type"),
            "command":      rec.get("command"),
            "soc_pct":      soc,
            "pv_watts_in":  pv,
            "ac_watts_out": ac,
            "dc_watts_out": dc,
        }
        print(json.dumps(out))

if __name__ == "__main__":
    main()

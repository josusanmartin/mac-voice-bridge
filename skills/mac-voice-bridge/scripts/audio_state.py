#!/usr/bin/env python3
"""CoreAudio metadata snapshots and explicit restoration; no audio streams."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import platform
import sys

SELECTORS = {"input": "dIn ", "output": "dOut", "alerts": "sOut"}


def fourcc(text):
    return int.from_bytes(text.encode("ascii"), "big")


class Address(C.Structure):
    _fields_ = [("selector", C.c_uint32), ("scope", C.c_uint32),
                ("element", C.c_uint32)]


class CoreAudio:
    def __init__(self):
        if platform.system() != "Darwin":
            raise RuntimeError("CoreAudio metadata requires macOS")
        self.ca = C.CDLL("/System/Library/Frameworks/CoreAudio.framework/CoreAudio")
        self.cf = C.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.ca.AudioObjectGetPropertyDataSize.argtypes = [C.c_uint32, C.POINTER(Address), C.c_uint32, C.c_void_p, C.POINTER(C.c_uint32)]
        self.ca.AudioObjectGetPropertyData.argtypes = [C.c_uint32, C.POINTER(Address), C.c_uint32, C.c_void_p, C.POINTER(C.c_uint32), C.c_void_p]
        self.ca.AudioObjectSetPropertyData.argtypes = [C.c_uint32, C.POINTER(Address), C.c_uint32, C.c_void_p, C.c_uint32, C.c_void_p]
        for name in ("AudioObjectGetPropertyDataSize", "AudioObjectGetPropertyData", "AudioObjectSetPropertyData"):
            getattr(self.ca, name).restype = C.c_int32
        self.cf.CFStringGetCString.argtypes = [C.c_void_p, C.c_char_p, C.c_long, C.c_uint32]
        self.cf.CFStringGetCString.restype = C.c_bool
        self.cf.CFRelease.argtypes = [C.c_void_p]

    def read(self, obj, selector, scope="glob"):
        address = Address(fourcc(selector), fourcc(scope), 0)
        size = C.c_uint32()
        status = self.ca.AudioObjectGetPropertyDataSize(obj, C.byref(address), 0, None, C.byref(size))
        if status:
            raise RuntimeError(f"CoreAudio metadata unavailable (OSStatus {status})")
        buffer = C.create_string_buffer(max(size.value, 1))
        status = self.ca.AudioObjectGetPropertyData(obj, C.byref(address), 0, None, C.byref(size), buffer)
        if status:
            raise RuntimeError(f"CoreAudio metadata unavailable (OSStatus {status})")
        return buffer.raw[:size.value]

    def scalar(self, obj, selector):
        raw = self.read(obj, selector)
        if len(raw) != 4:
            raise RuntimeError("Unexpected CoreAudio integer size")
        return C.c_uint32.from_buffer_copy(raw).value

    def string(self, obj, selector):
        raw = self.read(obj, selector)
        if len(raw) != C.sizeof(C.c_void_p):
            raise RuntimeError("Unexpected CoreAudio string pointer size")
        pointer = C.c_void_p.from_buffer_copy(raw)
        if not pointer.value:
            raise RuntimeError("Missing CoreAudio string")
        buffer = C.create_string_buffer(4096)
        try:
            if not self.cf.CFStringGetCString(pointer, buffer, len(buffer), 0x08000100):
                raise RuntimeError("Cannot decode CoreAudio string")
            return buffer.value.decode("utf-8")
        finally:
            self.cf.CFRelease(pointer)

    def inventory(self):
        raw = self.read(1, "dev#")
        if not raw or len(raw) % 4:
            raise RuntimeError("No usable devices returned; sandbox access may be restricted")
        devices = []
        for offset in range(0, len(raw), 4):
            device = C.c_uint32.from_buffer_copy(raw[offset:offset + 4]).value
            devices.append({"id": device, "uid": self.string(device, "uid "),
                            "name": self.string(device, "lnam")})
        return {"devices": devices,
                "defaults": {key: self.scalar(1, selector) for key, selector in SELECTORS.items()}}

    def set_default(self, key, device):
        address = Address(fourcc(SELECTORS[key]), fourcc("glob"), 0)
        value = C.c_uint32(device)
        status = self.ca.AudioObjectSetPropertyData(1, C.byref(address), 0, None, C.sizeof(value), C.byref(value))
        if status:
            raise RuntimeError(f"Cannot restore {key} (OSStatus {status})")


def current_uids(inventory):
    ids = {device["id"]: device["uid"] for device in inventory["devices"]}
    if len(ids) != len(inventory["devices"]):
        raise RuntimeError("Ambiguous device IDs")
    return {key: ids[inventory["defaults"][key]] for key in SELECTORS}


def make_snapshot(backend):
    return {"version": 1, "defaults": current_uids(backend.inventory())}


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
        raise ValueError("Unsupported snapshot")
    defaults = snapshot.get("defaults")
    if not isinstance(defaults, dict) or set(defaults) != set(SELECTORS):
        raise ValueError("Snapshot must include input, output, and alerts")
    if any(not isinstance(uid, str) or not uid or len(uid) > 4096 for uid in defaults.values()):
        raise ValueError("Invalid snapshot device UID")


def write_snapshot(path, snapshot):
    validate_snapshot(snapshot)
    # Exclusive creation protects the original baseline and rejects symlinks.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2)
        handle.write("\n")


def restore(backend, snapshot, apply=False):
    validate_snapshot(snapshot)
    before = backend.inventory()
    live = current_uids(before)
    devices = {}
    for device in before["devices"]:
        devices.setdefault(device["uid"], []).append(device["id"])
    errors, changed = [], []
    for key, uid in snapshot["defaults"].items():
        if live[key] == uid:
            continue
        candidates = devices.get(uid, [])
        if len(candidates) != 1:
            errors.append(f"{key}: original device unavailable or ambiguous; reconnect it or select manually")
            continue
        changed.append(key)
        if apply:
            try:
                backend.set_default(key, candidates[0])
            except RuntimeError as error:
                errors.append(str(error))
    verified = current_uids(backend.inventory()) if apply else live
    return {"mode": "apply" if apply else "preview", "changes": changed,
            "restored": verified == snapshot["defaults"], "errors": errors}


def main(argv=None, backend_factory=CoreAudio):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("inspect", help="Read metadata; includes private names and IDs")
    snapshot = actions.add_parser("snapshot", help="Write private rollback baseline; never overwrite")
    snapshot.add_argument("path", type=Path)
    restoration = actions.add_parser("restore", help="Preview restoration unless --apply is supplied")
    restoration.add_argument("path", type=Path)
    restoration.add_argument("--apply", action="store_true")
    state = restoration.add_mutually_exclusive_group()
    state.add_argument("--call-ended", action="store_true", help="Operator confirms phone call has ended")
    state.add_argument("--emergency", action="store_true", help="Break feedback now; hang up phone promptly")
    args = parser.parse_args(argv)
    if args.action == "restore" and args.apply and not (args.call_ended or args.emergency):
        parser.error("Hang up first, then add --call-ended; use --emergency for immediate feedback recovery")
    try:
        # Validate the file before opening CoreAudio, even for previews.
        saved = None
        if args.action == "restore":
            saved = json.loads(args.path.read_text(encoding="utf-8"))
            validate_snapshot(saved)
        backend = backend_factory()
        if args.action == "inspect":
            print(json.dumps(backend.inventory(), indent=2))
        elif args.action == "snapshot":
            write_snapshot(args.path, make_snapshot(backend))
            print("Private snapshot saved. This does not save browser selections or audio.")
        else:
            result = restore(backend, saved, args.apply)
            print(json.dumps(result, indent=2))
            if result["errors"] or (args.apply and not result["restored"]):
                return 1
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"Audio state error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

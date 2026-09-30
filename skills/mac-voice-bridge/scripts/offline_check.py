#!/usr/bin/env python3
"""Synthetic route model only: no device access, playback, recording, or files."""
import json
import math
import sys

RATE = 48000


def tone(frequency, amplitude=0.08):
    return [amplitude * math.sin(2 * math.pi * frequency * n / RATE) for n in range(RATE // 5)]


def amplitude(samples, frequency):
    real = sum(value * math.cos(2 * math.pi * frequency * n / RATE) for n, value in enumerate(samples))
    imag = sum(value * math.sin(2 * math.pi * frequency * n / RATE) for n, value in enumerate(samples))
    return 2 * math.hypot(real, imag) / len(samples) if samples else 0.0


def isolated(samples, wanted, unwanted):
    signal, leakage = amplitude(samples, wanted), amplitude(samples, unwanted)
    return signal >= 0.01 and leakage <= signal * 10 ** (-50 / 20)


def valid_routes(a, b):
    return isolated(a, 440, 880) and isolated(b, 880, 440)


def check():
    a, b = tone(440), tone(880)
    mixed = [x + y for x, y in zip(a, b)]
    silence = [0.0] * len(a)
    leaking_a = [x + 0.01 * y for x, y in zip(a, b)]
    return {"independent_routes_accepted": valid_routes(a, b),
            "mixed_routes_rejected": not valid_routes(mixed, mixed),
            "swapped_routes_rejected": not valid_routes(b, a),
            "silence_rejected": not valid_routes(silence, silence),
            "minus_40_db_leakage_rejected": not valid_routes(leaking_a, b)}


if __name__ == "__main__":
    results = check()
    print(json.dumps({"mode": "offline synthetic model", "checks": results}, indent=2))
    sys.exit(0 if all(results.values()) else 1)

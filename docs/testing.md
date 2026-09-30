# Test evidence and limits

## Original observed experiment

The September 30, 2026 experiment used one Apple Silicon Mac, official BlackHole 2ch and 16ch version 0.7.1, existing 48 kHz rates, Brave, Google Voice, and dot in the Codex Mac app. Exact OS/browser/app versions were not collected in this public summary. Results are operator observations and sanitized technical summaries; raw private artifacts are not distributed.

1. An offline Web Audio graph accepted independent 440/880 Hz paths and rejected mixing, swapping, and silence. This established detector behavior, not hardware behavior.
2. A 6.4-second real-device synthetic test opened only the first stereo pair of each virtual device. Each bus returned its own tone; the other remained quiet. Both together passed a 50 dB opposite-tone rejection threshold. There were zero reported PortAudio callback flags; defaults and rates were preserved. These short tests do not establish long-run performance.
3. Google Voice's local speaker test reached BlackHole 16ch. A varying synthetic harmonic signal with pauses on 2ch registered on its microphone meter. A prior pure 440 Hz probe did not register. Voice processing or filtering was not isolated as the cause.
4. A generated spoken fixture through 16ch reached dot while the operator confirmed remaining silent. macOS default output 2ch/input 16ch and separate supported alert output were observed.
5. On an authorized call to a consenting endpoint, the phone participant explicitly confirmed hearing dot, and dot heard the participant via Google Voice. The call announced 1 cent per minute. A later recovered-tab microphone prompt needed manual approval.
6. Audio defaults were restored by the main process and an independent experimental recovery worker. An initial setup-based 65-second window restored early, before hangup. This demonstrated a timing failure, not phone-service teardown.

No private audio was saved by the experiment scripts. Service audio processing and retention remain separate from local script behavior. No official integration, broad compatibility, emergency-calling suitability, unattended operation, latency bound, or long-duration stability is claimed.

## Checks for this public package

The published scripts were rewritten for portability and limited scope; they are not a verbatim copy of the machine-specific test harness. Run:

```sh
python3 skills/mac-voice-bridge/scripts/offline_check.py
python3 -m unittest discover -s tests -v
```

The detector checks independent paths and rejects mixing, reversal, silence, and -40 dB leakage against a -50 dB threshold. Mocked CoreAudio tests cover restoration after numeric IDs change, preview without mutation, missing/ambiguous devices, partial failures, wrong readback, invalid snapshots, snapshot overwrite protection, private file permissions, and the explicit apply/hangup declaration boundary.

Tests instantiate no real CoreAudio backend. They play no sound, open no microphone or virtual audio stream, grant no permission, install nothing, access no browser, and make no phone call. Snapshot tests use temporary files with invented identifiers. CI repeats these checks on Python 3.9 and 3.13 on Linux.

The optional macOS helper still requires validation in a user's permitted execution context before relying on it. Its actual restoration behavior was not rerun against the live Mac for this publication; the original CoreAudio experiment and the public mocked tests provide different kinds of evidence.

## Reporting another reproduction

Provide hardware architecture and software versions, which stage passed, approximate connected duration, any errors, and whether macOS **and** browser restoration was verified. Describe failures without sharing snapshots, unique devices, destinations, account identifiers, transcripts, or audio. A successful short call is useful evidence, but should not be generalized beyond the tested configuration.

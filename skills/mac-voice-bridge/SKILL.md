---
name: mac-voice-bridge
description: Set up, explain, troubleshoot, or restore an experimental Mac voice-assistant to browser-call audio bridge using two independent BlackHole devices. Use for local macOS audio routing, not native assistant dialing or unattended calling.
---

# Mac Voice Bridge

Use [references/workflow.md](references/workflow.md) for replication and [references/troubleshooting.md](references/troubleshooting.md) when a stage fails. This is a single-environment experiment with dot in the Codex Mac app and Google Voice, not an official integration or general compatibility promise.

## Essential routing

- Assistant output → macOS default output → BlackHole 2ch → browser microphone.
- Browser speakers → BlackHole 16ch → macOS default input → assistant input.
- Browser microphone and speakers must select their devices explicitly; using Default breaks isolation when the Mac defaults change.
- Keep ringing and supported system alerts on a separate physical output. Other default-output app audio can reach the call. Physical microphone access and local speaker monitoring are displaced by the bridge defaults.

## Workflow boundaries

Explain or inspect first. Run `scripts/offline_check.py` without hardware access. `scripts/audio_state.py inspect` reads metadata only; keep names/UIDs local. Snapshot actual current defaults to a private session-specific file before a change, and privately note browser selections. Do not assume the previous session's defaults.

Follow existing explicit authorization; ask only for missing authority before administrator installation, security or microphone permission grants, routing disruption, restarting apps/services or the Mac, an identified phone call, or a charge. Setup approval does not authorize dialing or recording. A recovered tab can prompt for microphone access again; let the user resolve it explicitly. Do not automatically reboot or close running jobs for a driver install.

Validate two unused independent virtual buses with synthetic signals before a live call. Do not open a virtual input carrying private audio merely to test it. A pure-tone meter failure is inconclusive; speech-like synthetic input succeeded in the observed app, but filtering is only a hypothesis. Verify each app follows the selected device rather than assuming it does.

Keep setup timeout, confirmed connected-call duration, and emergency routing deadline separate. There is no automated timer or watchdog in the packaged helper. Before a supervised call, identify the endpoint, participant consent, rate, duration, and recovery method. Do not claim the assistant natively dials or attaches to a phone call.

## Teardown

Ask before normal hangup unless the user's instruction already authorizes it. Hang up through the phone service, verify disconnection, then restore macOS and browser selections. Audio rollback never ends billing. For feedback, break the route immediately under the agreed emergency plan and promptly end the phone call.

The optional helper previews restoration by default:

```sh
python3 scripts/audio_state.py restore <private-snapshot>
python3 scripts/audio_state.py restore <private-snapshot> --apply --call-ended
```

`--call-ended` declares operator confirmation; it does not inspect the service. `--emergency` is available for urgent route recovery. The helper restores input/output/alert defaults by UID and checks readback, but does not save browser choices, rates, gain, or permissions. If an original device is disconnected, reconnect it or manually select a physical fallback and report incomplete restoration.

Report which stage was actually demonstrated. Separate the original observed experiment from this invocation's tests. Never claim compatibility or successful recovery based only on a mock. Keep private recordings, transcripts, snapshots, device identifiers, accounts, and phone numbers out of public deliverables.

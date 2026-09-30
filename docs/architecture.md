# Architecture and packaging

The bridge uses macOS as the patch bay. A virtual device receives samples written to its output and exposes them to readers of its input. Two separately installed BlackHole variants provide two buses; renaming or exposing a mirror of one variant does not separate directions.

The first bus carries the assistant's voice to the browser microphone. The second carries the browser speaker audio to the assistant microphone. Google Voice's explicit selections prevent its return audio from following the Mac's default output back into its own microphone.

This route has several distinct layers:

| Layer | Responsibility | Evidence required |
| --- | --- | --- |
| Driver | Two independent sample paths | Device-specific synthetic input/output tests |
| Browser app | Explicit microphone/speaker selection | Local output test and input meter |
| Assistant app | Uses chosen input/output | Attributed generated phrase and output check |
| Phone service | Connects and terminates the call | Operator-visible connected/disconnected states |
| Operator | Consent, cost, timing, and recovery | Explicit decisions and verified teardown |

Success at one layer does not prove the next. In particular, neither an offline model nor a microphone meter proves a remote person can hear the signal. Conversely, confirmed one-environment phone audio does not establish general stability or compatibility.

## Why a skill first

A skill can preserve the route map, permission boundaries, stage-specific tests, timer distinction, and recovery order while adapting to the user's apps. The self-contained skill includes a workflow, troubleshooting reference, a no-device synthetic model, and a portable metadata/restore helper.

It needs no browser extension, secret, remote service, or account integration. A browser extension can help with a site's UI but cannot independently create OS virtual microphones and speakers or make a desktop assistant use them. A plugin could distribute the same skill later. Without a mature native routing component or supported call interface, a plugin scaffold would primarily add packaging rather than capability, so none is included.

## Helper design

`audio_state.py` uses public CoreAudio property APIs via Python `ctypes`. It reads metadata only until the operator explicitly requests restoration with `--apply`. It snapshots stable UIDs for input, output, and alert output rather than assuming numeric IDs remain valid. Snapshots are private, exclusive-created files, and malformed files are rejected before any device mutation.

Restoration resolves current numeric IDs, attempts available defaults even when another original device is missing, and checks the resulting UIDs. Duplicate UIDs, failed writes, absent devices, and wrong readback prevent a successful result. There is no atomic transaction across the three settings, so partial restoration is reported and manual recovery remains necessary. The helper cannot restore browser choices, rates, gains, or permissions.

The helper deliberately provides no route activation or automatic watchdog. The original experiment's watchdog is described as evidence, but its setup-based 65-second deadline was unsuitable as a connected-call timer. A packaged restoration command must not imply that it terminates the phone connection.

## Work needed before broader automation

- Validate across documented macOS, app, browser, and driver versions, including session device retention and 16ch acceptance.
- Test longer operation, latency, overlap, acoustic feedback, and delayed echo with consenting endpoints.
- Design an app-specific output route if isolation from unrelated default-output apps is required.
- If adding automated activation, validate preconditions, independent recovery-worker readiness, cancellation, process death, and ownership of concurrent routing changes.
- Keep a phone-service connection/hangup interface separate from routing, use only supported authorized interfaces, and prove billing termination independently.
- Add setup and connected-call state handling rather than a single elapsed timer. Any emergency route guard should expose its independent deadline and recovery limitations.

These are proposed follow-ups, not implemented capabilities.

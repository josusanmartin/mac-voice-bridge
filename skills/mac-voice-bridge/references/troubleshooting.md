# Troubleshooting

Work on local tests first; do not redial repeatedly to debug a device selection.

| Symptom | Check and recovery |
| --- | --- |
| BlackHole missing | Verify the installed variant and Audio MIDI Setup inventory. Resolve installer requirements during a maintenance window; do not automatically reboot or restart CoreAudio. |
| Helper cannot enumerate devices | The process may be sandboxed. Compare with Sound settings; metadata failure is not evidence that no devices exist. Use manual notes/restoration if needed. |
| Browser microphone prompt reappears | A recovered tab or changed browser context can require site permission again. Let the user resolve the actual prompt; do not bypass it. |
| Browser rejects 16ch | Verify channels 1–2 and app support. Restore routing if incompatible. A different stereo virtual-device design is a new experiment, not an automatic substitute. |
| Browser microphone meter stays quiet for a tone | Pure 440 Hz failed in the observed meter, but synthetic speech-like audio passed. Check the explicit device, gain, permissions, and a safe generated speech-like fixture. Filtering is unproven. |
| Assistant hears the local user instead of the fixture | It may retain its original input. Verify defaults, restart only its authorized voice session if needed, and repeat a generated phrase while the operator stays silent. |
| Remote person hears unrelated media | Other apps share macOS default output. Pause them, suppress notifications, and verify alert routing. For stronger isolation, separately evaluate app-specific capture. |
| User cannot hear dot on Mac | Expected with output routed to 2ch. The phone participant may still hear it. Add only an approved independent headphone monitor; do not connect the monitor mix back to an input. |
| Dot cannot hear the physical microphone | Expected with default input set to 16ch. Restore the baseline or deliberately design an approved isolated mix. |
| Feedback or repeating voice | Check that browser microphone is 2ch and speakers 16ch explicitly. Break routing immediately under the emergency plan and hang up promptly. Acoustic feedback and delayed service echo also need investigation. |
| Route works briefly, then drops | A setup-based guard may have elapsed; check its deadline separately from call duration. The public helper starts no timers. Check device selection retention and session changes. |
| Glitches after adding monitoring | Aggregate/multi-output clocks, rates, or drift settings may need review. Return to the simple two-device route; monitoring was not validated by the base experiment. |
| Audio restores but phone call continues | Restoration is not hangup. End the call through the service and confirm disconnection. Charges may continue until it ends. |
| Restore reports missing original device | Reconnect the original device or manually choose a physical fallback. The helper attempts the other available defaults and reports incomplete recovery. |
| Restore returns errors or wrong readback | Use Sound settings and your baseline notes. There is no transactional CoreAudio restore; partial restoration is possible. Do not run a paid call while recovery remains uncertain. |
| macOS restored, browser still on BlackHole | Browser choices are independent and are not captured by the helper. Restore all three selections from your private notes. |

For public bug reports, provide versions and anonymized stage outcomes. Do not include device UIDs, phone/account/email identifiers, private snapshots, recordings, screenshots of signed-in pages, or transcripts. A local permission prompt is evidence of access needed; it is not permission for an agent to grant it.

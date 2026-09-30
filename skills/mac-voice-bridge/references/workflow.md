# Replication procedure

This procedure describes a supervised experiment. It does not configure unattended calling. Use the route table in this guide even if the UI labels differ between versions.

## 1. Establish a safe starting point

Finish unrelated calls and audio work first. Confirm which changes are authorized, who controls hangup, who will participate, and whether the call can cost money. Keep a physical output and microphone available for recovery. Close or pause sources that could leak notifications or media into the phone call.

Run the offline synthetic check from the cloned repository. It verifies the detector can distinguish two independent paths from mixing, reversal, silence, and excessive leakage. It does not touch hardware and does not establish installed-device isolation.

```sh
python3 skills/mac-voice-bridge/scripts/offline_check.py
python3 -m unittest discover -s tests -v
```

## 2. Install the two independent virtual drivers

Use the [official BlackHole project](https://github.com/ExistentialAudio/BlackHole) and its linked installer. Install both **2ch** and **16ch** variants. The original experiment used 0.7.1; obtain any historical version only through an official source. Do not assume a current package is the tested version.

If Homebrew is already installed and you approve the installation, its official package route is:

```sh
brew install --cask blackhole-2ch blackhole-16ch
```

Review any administrator authentication and installer prompts yourself. Do not weaken macOS system security for this workflow. Schedule any requested app closure or restart after running jobs have finished. The two devices appeared without a reboot in the observed environment; this is not a promise that another installer or Mac will behave the same way.

Open **Audio MIDI Setup** and confirm that BlackHole 2ch and BlackHole 16ch are separate devices with input and output. Observe sample rates before changing anything. The experiment kept both at their existing 48 kHz rates and used channels 1–2. If rates differ, stop and agree a matching configuration outside live audio work. Do not create an aggregate or multi-output device merely to reproduce the base route.

## 3. Capture a private recovery baseline

Record the current Sound input, output, and alert output; the browser's microphone, speakers, and ringing; and any gain or rate you intend to change. These may differ from the built-in defaults. The optional metadata helper reads current CoreAudio state without opening streams:

```sh
mkdir -p .runtime
python3 skills/mac-voice-bridge/scripts/audio_state.py inspect
python3 skills/mac-voice-bridge/scripts/audio_state.py snapshot .runtime/before.json
python3 skills/mac-voice-bridge/scripts/audio_state.py restore .runtime/before.json
```

Use a new snapshot filename for a new session. The snapshot never overwrites an old baseline. Keep it local; it contains device UIDs. The preview should report no changes when the baseline is current. If inspection returns an error or no devices, it may reflect process sandbox restrictions. Compare with Sound settings; do not infer that the Mac lacks devices, escalate permissions automatically, or start routing without a recovery baseline.

The helper saves only CoreAudio input/output/alert defaults. Browser selections and other configuration must be restored separately using your private notes. Keep the manual settings route available even when using the helper.

## 4. Validate unused paths with generated audio

Do this with no phone call and no private conversation routed to the virtual devices. Obtain any needed microphone access explicitly before opening a meter. Virtual inputs may require microphone permission too.

The original experiment used generated 440 and 880 Hz tones through device-specific PortAudio streams and inspected numerical summaries. It first checked each bus alone, then both together. The packaged offline check is a portable mathematical model; the original machine-specific PortAudio loader is intentionally not included.

For a manual hardware check, use an audio application you trust that allows **explicit output-device selection**, plus an input meter that allows explicit device selection. Disable input monitoring and recording. Do not use a player's system-default output for this stage.

1. Send a low-level generated 440 Hz signal to BlackHole 2ch, channels 1–2. Its input meter should respond; the 16ch input should remain quiet.
2. Stop it. Send 880 Hz to BlackHole 16ch, channels 1–2. Only that device's input should respond.
3. If your tools support simultaneous explicit outputs and spectral meters, send both. Each input should contain its own tone, with at least 50 dB rejection of the other. Ordinary level meters alone do not prove this quantitative threshold.
4. Stop all generators and close test streams. Check that defaults and sample rates still match your baseline.

Do not intentionally cross-mix a live graph for a negative control. The offline check supplies safe fault controls. Do not open or save a stream containing real conversation just to diagnose a path.

## 5. Validate Google Voice locally

Open Google Voice and its audio settings. Select **microphone = BlackHole 2ch**, **speakers = BlackHole 16ch**, and **ringing = a separate physical output**, explicitly rather than Default. Resolve browser/site and macOS microphone permissions yourself. A recovered tab may request access again even if a previous tab worked.

Use the local speaker Test button and a BlackHole 16ch meter to confirm the return path, then stop that test. For the microphone meter, feed a low-level synthetic speech-like signal into 2ch with your explicitly selected sender. The experiment's pure 440 Hz input did not appear in the Google Voice meter, while varying harmonics with pauses did. Filtering or voice processing is a hypothesis, not an established cause.

An optional spoken fixture can be generated locally without recording a person:

```sh
say -o .runtime/synthetic-phrase.aiff "Virtual audio routing test. The blue lantern is ready."
```

Import that generated file into the explicit-output sender. A generic media player may use the wrong output. Meter success demonstrates local reception; it does not by itself prove transmission to a phone.

## 6. Select the Mac defaults and verify the assistant

With routing disruption authorized, use **System Settings → Sound**:

| Control | Selection |
| --- | --- |
| Output | BlackHole 2ch |
| Input | BlackHole 16ch |
| Alert/sound-effect output, if independently available | Built-in physical output |

Confirm the browser still selects its explicit devices. Start or refresh the assistant voice session only as authorized; some apps keep the device selected when their session started. Do not assume every assistant follows a default change mid-session.

For an input attribution check with no phone participant, send the generated spoken fixture explicitly into 16ch while the operator stays silent. Ask the assistant what it heard and distinguish the fixture from physical-microphone input. For output, ask for a brief nonsensitive phrase and observe the browser's 2ch microphone meter. This stage passes only if each actual app responds. Restore the baseline if either fails.

This replaces the assistant's normal physical microphone and speaker paths. An optional headphone monitor needs a separate, deliberately configured copy of the buses. Never feed that monitor mix back into either bus. Monitoring and physical-microphone mixing were not required or proven by the base experiment.

## 7. Run a short consenting phone test

Identify the exact destination privately, confirm participant consent to AI audio, review the displayed/announced rate, and approve the call and any charge. Let the operator place the call; this bridge has no dialing API. Start the connected-call timer when Google Voice reports connection, not when setup starts.

Verify the remote person hears the assistant and the assistant hears the remote person. Test one direction first, then brief turn-taking. Do not assume that direct wiring isolation solves delayed echo, overlapping speech, or service voice detection. If feedback occurs, break routing under the emergency plan and promptly hang up.

## Timing and teardown

Agree these independently before calling:

| Clock/action | Start and purpose |
| --- | --- |
| Setup timeout | Starts with configuration; abort preparation if devices or permissions remain unresolved |
| Connected-call timer | Starts on actual connection; tracks the agreed test duration and possible charges |
| Optional routing guard | A separately agreed emergency deadline; can restore audio but cannot hang up |
| Normal hangup | Ask before ending unless the user already authorized that action; execute through the phone service |

The experimental guard used 65 seconds measured from routing setup. Permission/setup delay consumed that window, so it restored audio before the connected test had finished. Do not reproduce that timing design. This release includes no automatic routing guard. If you add one, it needs independent verification, an explicit emergency purpose, a visible deadline, and phone-service teardown coordination. Do not silently extend a deadline or treat restoration as disconnection.

At the agreed endpoint, obtain any still-required normal-hangup approval, then:

1. **Hang up in Google Voice or at the phone endpoint.** Confirm the service shows the call is disconnected.
2. Restore macOS defaults manually or use the optional helper:

   ```sh
   python3 skills/mac-voice-bridge/scripts/audio_state.py restore .runtime/before.json --apply --call-ended
   ```

3. Restore the browser's microphone, speakers, and ringing from private notes. Stop test playback and any monitors.
4. Check that the physical microphone and output work again and that supported alert output matches the baseline. Review the phone service's disconnected state once more.

For an urgent feedback incident, restoration can use `--apply --emergency` before hangup confirmation. Audio interruption is then intentional; manually hang up promptly because billing can continue. The helper is not a watchdog and will not recover a killed process automatically. If restoration reports a missing device, reconnect it or select a physical fallback manually; never claim full recovery until verified.

## Removing the setup

End phone and assistant sessions and restore the baseline before uninstalling drivers. Follow the vendor's current uninstaller instructions during a safe maintenance window. Removing a driver, restarting CoreAudio, or rebooting can interrupt unrelated audio work and requires its own authorization. Uninstalling this skill only removes its directory; it does not remove BlackHole or change Sound settings.

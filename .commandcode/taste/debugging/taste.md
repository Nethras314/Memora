# Debugging

- Verify empirically before drawing a conclusion. "The server is running" is not evidence the feature works — actually exercise it (build the bundle, hit the exact endpoint, check status codes and payload sizes).
- Check a failing probe isn't your own test artifact before chasing it. A 404 from a hand-typed URL may just be the wrong path, not a real bug; confirm against the URL the client actually requests.
- When the user reports a vague symptom, ask a targeted multiple-choice question about the exact visible error and the environment before changing anything. Options like "red error screen / login spins / blank screen / can't reach Metro" resolve in one round trip where guessing takes many.
- Rule the code out explicitly before blaming the environment. Building the bundle cleanly is strong evidence the app source is fine — say so rather than speculating about code.
- Name the single root cause plainly, and state what was ruled out and why.
- Delete every temporary artifact as soon as it's served its purpose: debug export dirs, log files, one-off scripts. Don't leave them in the repo.
- After making a fix, re-verify that it actually landed (e.g. re-run the version check) and that the service came back up. Don't assume the change took effect.
- If a command fails or an approach stalls, change approach rather than re-issuing the same call.

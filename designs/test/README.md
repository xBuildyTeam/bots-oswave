# Wave bot design test set (wave.avatar/1)

`wave-avatar-vectors.json` holds the 11 official bot designs as read from Theta, with what each one must draw.
Every Wave system (Wave Web, Wave OS, Wave desktop, the Wave | Bots plugin for Hermes) checks its design reader against this file.

The one rule: in a `pixel20` design, pixel value `0` is empty (transparent) and value `n` is `palette[n-1]`.

URL: https://bots.oswave.io/designs/test/wave-avatar-vectors.json

"""Generate placeholder game sounds into ../assets (standard library only).

Run:  python3 tools/make_sounds.py
Replace any of the .wav files with real samples later; keep the same names.
"""
import math
import os
import random
import struct
import wave

RATE = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def write(name, samples):
    peak = max(abs(s) for s in samples) or 1.0
    with wave.open(os.path.join(OUT, name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(32000 * s / peak)) for s in samples))


def kick(dur=0.4):
    out, phase = [], 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        freq = 45 + 110 * math.exp(-t * 30)  # pitch drops fast: the "boom"
        phase += 2 * math.pi * freq / RATE
        click = math.exp(-t * 400) * 0.4
        out.append(math.sin(phase) * math.exp(-t * 9) + click)
    return out


def snare(dur=0.25):
    out, last = [], 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        noise = random.uniform(-1, 1)
        bright = noise - last  # crude high-pass: keeps the "tss"
        last = noise
        tone = math.sin(2 * math.pi * 190 * t) * math.exp(-t * 35)
        out.append(bright * math.exp(-t * 18) * 0.7 + tone * 0.6)
    return out


def hihat(dur=0.08):
    out, last = [], 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        noise = random.uniform(-1, 1)
        bright = noise - last  # high-pass twice: only the "tss"
        last = noise
        out.append(bright * math.exp(-t * 60))
    return out


def click(freq, dur=0.03):
    return [math.sin(2 * math.pi * freq * i / RATE) * math.exp(-i / RATE * 120) for i in range(int(dur * RATE))]


# Sung notes, as MIDI numbers: A minor pentatonic from A3 up to A4.
# Each note is rendered at its real pitch (not sped up), so the vowel stays natural.
VOICE_NOTES = [57, 60, 62, 64, 67, 69]

# The game loops the middle of each voice sample so a note can be held as
# long as needed. Keep these the same as VOICE_LOOP in sound-engine.js.
LOOP_START = 0.5   # seconds
LOOP_END = 2.5
LOOP_FADE = 0.1    # crossfade that hides the jump back to LOOP_START


def make_loopable(samples):
    """Blend the end of the loop into the audio just before its start,
    so jumping from LOOP_END back to LOOP_START has no click."""
    a, b, f = int(LOOP_START * RATE), int(LOOP_END * RATE), int(LOOP_FADE * RATE)
    out = list(samples)
    for i in range(f):
        w = i / f
        out[b - f + i] = samples[b - f + i] * (1 - w) + samples[a - f + i] * w
    return out


def midi_to_freq(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def voice(f0=220.0, dur=3.0):
    """An 'aah' at pitch f0: harmonics shaped by the vowel's formants, with a little vibrato.
    Long (3 s) so a note can be held while the mouth is open; the game fades it out early."""
    formants = [(800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.15)]

    def gain(f):
        return sum(a / (1 + ((f - fc) / bw) ** 2) for fc, bw, a in formants)

    harmonics = [(k, gain(k * f0) / k ** 0.5) for k in range(1, int(4000 / f0))]
    out, phase = [], 0.0
    for i in range(int(dur * RATE)):
        t = i / RATE
        phase += 2 * math.pi * f0 * (1 + 0.006 * math.sin(2 * math.pi * 5.5 * t)) / RATE
        env = min(1.0, t / 0.03) * min(1.0, (dur - t) / 0.3)   # steady: held notes don't fade
        out.append(env * sum(a * math.sin(k * phase) for k, a in harmonics))
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write("kick.wav", kick())
    write("snare.wav", snare())
    write("hihat.wav", hihat())
    write("click.wav", click(1500))
    write("click_hi.wav", click(2200))
    os.makedirs(os.path.join(OUT, "voice"), exist_ok=True)
    for note in VOICE_NOTES:
        write(os.path.join("voice", f"{note}.wav"), make_loopable(voice(midi_to_freq(note))))
    print("wrote sounds to", os.path.normpath(OUT))

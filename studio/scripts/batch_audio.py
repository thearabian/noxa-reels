"""Build VO timeline + original amapiano-style beat + SFX for each reel in a batch."""
import json, subprocess, sys, wave, math, numpy as np
D = sys.argv[1]; SR = 48000; FPS = 30
meta = json.load(open(f"{D}/vo/meta.json"))
BPM = 113; PER = 60 / BPM

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def trim(a):
    idx = np.where(np.abs(a) > 0.01)[0]
    s0 = max(0, idx[0] - int(.02 * SR)); s1 = min(len(a), idx[-1] + int(.06 * SR))
    return a[s0:s1], s0 / SR

def squeeze(a, words, maxgap=.24):
    env = np.convolve(np.abs(a), np.ones(480) / 480, mode="same") > .006
    out = []; shifts = []; i = 0; N = len(a)
    while i < N:
        j = i
        if not env[i]:
            while j < N and not env[j]: j += 1
            L = j - i; keep = min(L, int(maxgap * SR)); out.append(a[i:i + keep])
            if L > keep: shifts.append(((i + keep) / SR, (L - keep) / SR))
        else:
            while j < N and env[j]: j += 1
            out.append(a[i:j])
        i = j
    nt = lambda t: t - sum(c for at, c in shifts if at <= t)
    return np.concatenate(out), [dict(x, t=nt(x["t"])) for x in words]

def A(*xs):
    L = max(len(x) for x in xs); o = np.zeros(L)
    for x in xs: o[:len(x)] += x
    return o

def tone(f0, f1, d, decay=8, harm=0):
    k = np.arange(int(d * SR)) / SR; f = np.linspace(f0, f1, len(k)); ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + harm * np.sin(2 * ph) * .5 + harm * np.sin(3 * ph) * .25
    return y * np.exp(-k * decay)

def noise(d, decay=10, lp=.3, seed=0, hp=False):
    r = np.random.default_rng(seed); x = r.standard_normal(int(d * SR))
    y = np.zeros_like(x); acc = 0
    for i in range(len(x)): acc += lp * (x[i] - acc); y[i] = acc
    if hp: y = x - y
    return y * np.exp(-np.arange(len(x)) / SR * decay)

def pad_chord(freqs, d):
    k = np.arange(int(d * SR)) / SR; y = np.zeros(len(k))
    for f in freqs:
        for h, a in [(1, 1), (2, .35), (3, .15)]:
            y += a * np.sin(2 * np.pi * f * h * k + f) * (1 + .003 * np.sin(2 * np.pi * 5 * k))
    env = np.minimum(1, k / .25) * np.minimum(1, (d - k) / .3)
    return y * env / len(freqs)

NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)

def music(total, seed, root):
    r = np.random.default_rng(seed); n = int(total * SR); out = np.zeros(n)
    def put(t, x, g):
        i = int(t * SR)
        if i >= n or i < 0: return
        j = min(n, i + len(x)); out[i:j] += g * x[:j - i]
    kick = tone(150, 42, .4, 9); clap = A(noise(.18, 22, .6, 1, hp=True) * .8, noise(.05, 60, .9, 2) * .5)
    shk = noise(.06, 70, .9, 3, hp=True); rim = A(tone(1700, 1650, .05, 60), noise(.03, 90, .9, 4, hp=True) * .4)
    prog = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]]  # i VI III VII
    LOG = [0, 3, 6, 10, 11, 14] if seed % 2 else [0, 3, 7, 10, 12, 14]
    steps = int(total / (PER / 4)) + 1
    for s in range(steps):
        t = s * PER / 4; bar = s // 16; st = s % 16
        if st % 4 == 0: put(t, kick, .9)
        if st in (4, 12): put(t, clap, .35)
        put(t, shk, .10 if st % 2 else .06)
        if st in (3, 7, 11, 15) and r.random() < .6: put(t, rim, .12)
        if st in LOG:
            ch = prog[bar % 4]; nn = root - 12 + ch[(st // 4) % 3]
            f = NOTE(nn); x = tone(f * 1.6, f, .35, 7); x = np.tanh(x * 2.5) * .6
            put(t, x, .45)
        if st == 0:
            ch = prog[bar % 4]; put(t, pad_chord([NOTE(root + c) for c in ch], PER * 4), .11)
    fade = np.minimum(1, np.minimum(np.arange(n) / SR / .05, (total - np.arange(n) / SR) / .8))
    return out * np.clip(fade, 0, 1)

# ---------------- SFX library
def sfx_lib():
    d = {}
    d["pop"] = A(tone(700, 1300, .09, 28) * .5, noise(.04, 80, .8, 5) * .3)
    d["ding"] = A(tone(1568, 1568, .6, 6) * .4, tone(2349, 2349, .5, 8) * .2)
    d["chaching"] = A(tone(1318, 1318, .7, 4) * .35, tone(1760, 1760, .9, 3.5) * .3, tone(2637, 2637, .5, 6) * .15, noise(.08, 40, .7, 6) * .4)
    d["whoosh"] = noise(.45, 0, .2, 7) * np.sin(np.pi * np.linspace(0, 1, int(.45 * SR))) ** 2 * .9
    d["stamp"] = A(tone(120, 55, .35, 10) * .9, noise(.12, 30, .25, 8) * .7)
    d["buzz"] = A(*(tone(f, f, .35, 3, harm=1) * .25 for f in (110, 116)))
    d["tick"] = A(tone(3200, 3000, .03, 120) * .5, noise(.02, 150, .9, 9) * .3)
    d["ping"] = A(tone(1760, 1760, .25, 14) * .4, tone(2637, 2637, .3, 12) * .3)
    d["msg"] = A(tone(900, 1500, .07, 30) * .4, tone(1500, 1500, .12, 25) * .2)
    d["riser"] = (lambda k: noise(len(k) / SR, 0, .4, 10)[:len(k)] * (k / k[-1]) ** 2 * .5)(np.arange(1, int(.8 * SR)) / SR)
    d["boing"] = (lambda k: np.sin(2 * np.pi * np.cumsum(170 + 240 * np.sin(np.pi * k / .35) * (1 + .3 * np.sin(2 * np.pi * 14 * k))) / SR) * np.exp(-k * 5) * .5)(np.arange(int(.35 * SR)) / SR)
    k = np.arange(int(1.6 * SR)) / SR
    ring = np.sin(2 * np.pi * 440 * k) + np.sin(2 * np.pi * 480 * k); ring *= ((k % .4) < .3) * .18 * np.minimum(1, (1.6 - k) / .2)
    d["ring"] = ring
    d["hold"] = np.concatenate([tone(NOTE(n), NOTE(n), .18, 6, harm=.6) * .14 for n in [76, 79, 81, 79, 76, 72, 74, 76]])
    d["click"] = A(noise(.03, 120, .9, 11) * .5, tone(2400, 1800, .04, 60) * .3)
    d["sparkle"] = np.concatenate([tone(2093 * 2 ** (i / 6), 2093 * 2 ** (i / 6), .12, 14) * .1 for i in range(8)])
    return d

def wt(seg, word, nth=0):
    c = [x for x in seg["words"] if x["w"].lower().strip(".,?!") == word.lower()]
    return c[nth]["t"] if c else seg["start"]

# per-reel SFX cues: list of (sfx, time-fn)
CUES = {
 "callcentre": lambda S: [("ring", .0), ("stamp", wt(S["a"], "agents")), ("stamp", wt(S["a"], "salaries")), ("hold", S["b"]["start"] + .2), ("buzz", wt(S["b"], "hold")),
   ("click", S["c"]["start"] - .05), ("whoosh", S["c"]["start"] - .3), ("ding", wt(S["c"], "instantly")), ("ping", wt(S["c"], "three")), ("pop", wt(S["d"], "hold")), ("pop", wt(S["d"], "missed")), ("riser", S["e"]["start"] - .8), ("pop", wt(S["e"], "automate"))],
 "3am": lambda S: [("tick", .0), ("tick", PER), ("tick", 2 * PER), ("ping", wt(S["a"], "buy")), ("tick", S["b"]["start"]), ("msg", wt(S["c"], "replied")), ("msg", wt(S["c"], "answered")), ("msg", wt(S["c"], "question")),
   ("ding", wt(S["c"], "order")), ("whoosh", S["d"]["start"] - .3), ("chaching", wt(S["d"], "money")), ("sparkle", wt(S["d"], "money") + .2), ("pop", wt(S["e"], "automate"))],
 "website": lambda S: [("riser", 0.0), ("stamp", wt(S["b"], "one")), ("tick", wt(S["b"], "forever")), ("tick", wt(S["b"], "forever") + .3), ("tick", wt(S["b"], "forever") + .6), ("buzz", wt(S["b"], "load")),
   ("stamp", wt(S["c"], "two")), ("buzz", wt(S["c"], "template")), ("stamp", wt(S["d"], "three")), ("boing", wt(S["d"], "click")),
   ("whoosh", S["e"]["start"] - .3), ("sparkle", wt(S["e"], "feel")), ("pop", wt(S["f"], "save")), ("whoosh", wt(S["f"], "send"))],
 "pickone": lambda S: [("riser", 0.0), ("ding", wt(S["a"], "one")), ("stamp", S["b"]["start"]), ("stamp", S["c"]["start"]), ("stamp", S["d"]["start"]), ("pop", wt(S["e"], "comments")), ("riser", S["f"]["start"] - .8), ("chaching", wt(S["f"], "gift")), ("sparkle", wt(S["f"], "gift") + .15), ("stamp", wt(S["f"], "three")), ("ding", wt(S["f"], "key")), ("pop", wt(S["f"], "thousand")), ("stamp", wt(S["f"], "noxa")), ("ping", wt(S["f"], "twentyfour"))],
 # batch w48
 "whatsapp": lambda S: [("msg", .0), ("msg", .12), ("msg", .24), ("msg", .36), ("ping", wt(S["a"], "customer")), ("tick", wt(S["b"], "three")), ("buzz", wt(S["b"], "competitor")),
   ("whoosh", S["c"]["start"] - .3), ("msg", wt(S["c"], "replies")), ("msg", wt(S["c"], "all")), ("msg", wt(S["c"], "arabic")), ("msg", wt(S["c"], "english")), ("ding", wt(S["c"], "seconds")),
   ("pop", wt(S["d"], "prices")), ("pop", wt(S["d"], "stock")), ("pop", wt(S["d"], "delivery")), ("chaching", wt(S["d"], "booked")), ("riser", S["e"]["start"] - .8), ("pop", wt(S["e"], "automate"))],
 "employee": lambda S: [("stamp", .0), ("ding", wt(S["a"], "employee")), ("sparkle", wt(S["a"], "employee") + .1), ("stamp", wt(S["b"], "seven")), ("tick", wt(S["b"], "sick")),
   ("pop", wt(S["c"], "answers")), ("pop", wt(S["c"], "books")), ("pop", wt(S["c"], "follows")), ("stamp", wt(S["d"], "overtime")), ("stamp", wt(S["d"], "holidays")), ("stamp", wt(S["d"], "drama")),
   ("riser", S["e"]["start"] - .8), ("pop", wt(S["e"], "automate"))],
 "hours": lambda S: [("riser", 0.0), ("tick", wt(S["a"], "hours")), ("ding", wt(S["a"], "admin")), ("stamp", S["b"]["start"]), ("click", wt(S["b"], "spreadsheets")),
   ("stamp", S["c"]["start"]), ("msg", wt(S["c"], "five")), ("stamp", S["d"]["start"]), ("chaching", wt(S["d"], "payments")), ("riser", S["e"]["start"] - .8), ("pop", wt(S["e"], "number")), ("sparkle", wt(S["e"], "automate"))],
 "glowup": lambda S: [("whoosh", 0.0), ("stamp", wt(S["a"], "brand")), ("riser", S["b"]["start"] - .6), ("sparkle", wt(S["b"], "noxa")), ("whoosh", wt(S["c"], "jado")), ("whoosh", wt(S["c"], "genzy")),
   ("whoosh", wt(S["c"], "yalla")), ("ding", wt(S["d"], "remember")), ("pop", wt(S["d"], "use")), ("riser", S["e"]["start"] - .8), ("pop", wt(S["e"], "build"))],
}

SEEDS = {"callcentre": (1, 57), "3am": (2, 60), "website": (3, 62), "pickone": (4, 59),
         "whatsapp": (5, 58), "employee": (6, 61), "hours": (7, 57), "glowup": (8, 62)}
lib = sfx_lib()
ONLY=sys.argv[2:] or list(meta)
for reel, lines in meta.items():
    if reel not in ONLY: continue
    segs = []; parts = []; t = .12
    for i, ln in enumerate(lines):
        a, off = trim(load(f"{D}/vo/{reel}_{ln['key']}.mp3"))
        words = [dict(x, t=x["t"] - off) for x in ln["words"]]
        a, words = squeeze(a, words)
        if i > 0:
            n = math.ceil((t + .14) / (PER / 2)); t = n * PER / 2
        segs.append({"key": ln["key"], "text": ln["text"], "start": round(t, 3), "end": round(t + len(a) / SR, 3),
                     "words": [{"w": w["w"], "t": round(t + w["t"], 3), "d": round(w["d"], 3)} for w in words]})
        parts.append((t, a)); t += len(a) / SR
    total = round(math.ceil((t + 1.7) / PER) * PER, 3)
    n = int(total * SR); vo = np.zeros(n)
    for st, a in parts: i = int(st * SR); vo[i:i + len(a)] += a[:n - i]
    S = {s["key"]: s for s in segs}
    sfx = np.zeros(n)
    for name, at in CUES[reel](S):
        x = lib[name]; i = int(max(0, at) * SR); j = min(n, i + len(x)); sfx[i:j] += x[:j - i]
    seed, root = SEEDS[reel]
    mus = music(total, seed, root)
    venv = np.convolve(np.abs(vo), np.ones(int(.1 * SR)) / int(.1 * SR), mode="same")
    duck = 1 - .55 * np.clip(venv * 14, 0, 1)
    mix = vo * 1.0 + mus * .55 * duck + sfx * .9
    mix /= max(1, np.max(np.abs(mix)) / .95)
    with wave.open(f"{D}/{reel}.wav", "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix * 32767).astype(np.int16).tobytes())
    nf = int(total * FPS); spf = SR // FPS
    amp = [float(np.sqrt(np.mean(vo[i * spf:(i + 1) * spf] ** 2))) for i in range(nf)]; mx = max(amp)
    amp = [round(min(1, x / mx * 1.4), 3) for x in amp]
    beats = [round(k * PER, 3) for k in range(int(total / PER) + 1)]
    tl = {"reel": reel, "fps": FPS, "total": total, "frames": nf, "per": PER, "segs": segs, "amp": amp, "beats": beats}
    open(f"{D}/tl_{reel}.js", "w").write("window.TL=" + json.dumps(tl) + ";")
    json.dump(tl, open(f"{D}/tl_{reel}.json", "w"))
    print(reel, "total", total, [(s["key"], s["start"]) for s in segs])

# Recipes: Building Instruments with Pd-MCP-Server

These recipes are field notes from building generative instruments with the
Pd-MCP-Server, including the patch-side extensions we added and the pitfalls
we hit. Each recipe assumes the extended `example_patch.pd` from the
`feature/patch-extensions-and-recipes` branch.

## Patch-side extensions (what we added to example_patch.pd)

The stock patch routes `/pd/create`, `/pd/connect`, `/pd/dsp`, `/pd/clear`.
The MCP server advertises more tools (`save_patch`, `set_param`, ...) than the
patch can actually receive. We added these routes:

| Route | OSC format | What it does |
|---|---|---|
| `/pd/smsg` | `[name, ...args]` | Sends a message to a named `[r name]` receiver in the workspace. Chain: `list prepend list` → `list trim` → `t a a` → right: `list split 1` → `set $1` → `[send]`; left: `list split 1` → rest → `[send]` |
| `/pd/msg` | `[x, y, ...text]` | Creates a **message box** (vs. object box) in the workspace. Chain: `list prepend msg` → `list trim` → `s pd-workspace` |
| `/pd/save` | `[path]` | Saves the workspace subpatch to disk. Chain: `symbol` → `[; pd-workspace save $1(` → `s pd` |

### Critical pitfalls we learned the hard way

1. **OSC type tags matter.** `python-osc` sends Python strings as OSC strings →
   Pd symbols. An object created with a symbol arg where a float is expected
   comes out **dashed** (couldn't create), and faustgen~ params error with
   "parameter requires a float value". Always send `float(x)` for numbers.
2. **Message-box `$1` needs no backslash** when sent over OSC — send the plain
   string `"$1"`. Escaped `\$1` lands in the box literally and breaks
   substitution.
3. **Envelope messages** like `1, 0 120` must be separate float atoms
   `[1.0, ",", 0.0, 120.0]`, not strings.
4. **Object index drift**: `clear_workspace` resets the server's counter but
   reopening the patch in Pd without clearing leaves the server stale —
   always `clear_workspace` after reopening.
5. **`counter` and `demux` are NOT vanilla** — use a `f → + 1 → % N` feedback
   loop and `spigot` gates instead.
6. **faustgen~ (Pd port) loads .dsp via creation argument** (path, sans
   `.dsp` extension) — the `read` message from the Max version doesn't exist.

## Recipe 1: 440 Hz smoke test

```
create_object("osc~", ["440"], {x:100,y:100})   # args as strings OK here? NO - use floats via raw OSC
```

Better via raw OSC (correct types):

```python
from pythonosc.udp_client import SimpleUDPClient
c = SimpleUDPClient("127.0.0.1", 5000)
c.send_message("/pd/create", [100.0, 100.0, "osc~", 440.0])   # obj 0
c.send_message("/pd/create", [100.0, 200.0, "*~", 0.25])      # obj 1
c.send_message("/pd/create", [100.0, 300.0, "dac~"])          # obj 2
c.send_message("/pd/connect", [0.0, 0.0, 1.0, 0.0])
c.send_message("/pd/connect", [1.0, 0.0, 2.0, 0.0])
c.send_message("/pd/connect", [1.0, 0.0, 2.0, 1.0])
c.send_message("/pd/dsp", [1.0])
```

## Recipe 2: faustgen~ instrument with live parameter control

```python
# create faustgen~ with dsp file (absolute path, no extension!)
c.send_message("/pd/create", [100.0, 100.0, "faustgen~", "/path/to/mysynth"])
# a named receive wired to its left inlet
c.send_message("/pd/create", [100.0, 50.0, "r", "fg"])
c.send_message("/pd/connect", [1.0, 0.0, 0.0, 0.0])
# now control any FAUST parameter by name:
c.send_message("/pd/smsg", ["fg", "freq", 220.0])
c.send_message("/pd/smsg", ["fg", "gain", 0.8])
```

## Recipe 3: 16-step drum machine (vanilla Pd)

Pattern: `metro → f/+ 1/% 16` counter → `select` per drum → message box
`[1, 0 120(` → `line~` → `*~` VCA on a noise/sine source.

Groove switching: counter → 3 × `[spigot]`, gates driven by
`hradio → == 0/1/2` → each spigot feeds a different set of `select` boxes.

## Recipe 4: The dub machine (full rig)

See `recipes/dub_machine.py` for the complete build script:
- FAUST microtonal drone (8 golden-ratio-detuned panning sines)
- FAUST Sleng-Teng-style dub bass (saw+sub, resonlp, 4-shape LFO on cutoff)
- 16-step drums (kick/snare/hat)
- 3 switchable grooves
- Master ON toggle gating everything
- All voices → `*~ 0.4` → dac~

## Recipe 5: Persisting your work

With the `/pd/save` route, save the workspace any time:

```python
c.send_message("/pd/save", ["/path/to/my_patch.pd"])
```

Do this early and often — the dynamic workspace is ephemeral and dies with Pd.

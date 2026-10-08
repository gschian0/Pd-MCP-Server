#!/usr/bin/env python3
"""
Recipe: The Dub Machine
=======================
A complete generative dub rig built through Pd-MCP-Server OSC routes.

Components:
  - FAUST microtonal drone (beating.dsp): 8 golden-ratio detuned panning sines
  - FAUST dub bass (dubbass.dsp): Sleng-Teng style saw+sub -> resonant lowpass,
    gated by sequencer, 4-shape LFO (off/sine/tri/square/S&H) on the cutoff
  - Vanilla 16-step drums: kick (osc~ 55), snare (noise~), hat (noise~ + hip~)
  - 3 grooves switchable live: Sleng Teng / Steppers / Half-time dub
  - Master ON toggle gates everything (drone gain + bass gate)
  - All voices -> *~ 0.4 -> dac~ (fixed safe gain, mix downstream)

Requires: extended example_patch.pd (feature/patch-extensions-and-recipes
branch) with /pd/smsg and /pd/msg routes.

Usage:
  uv run python recipes/dub_machine.py            # build
  uv run python recipes/dub_machine.py --save out.pd   # build + save
"""

import argparse
import json
from pythonosc.udp_client import SimpleUDPClient

DSP_DIR = "/Users/user/Music/MCP/Pd-MCP-Server/dsp"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--dsp-dir", default=DSP_DIR)
    ap.add_argument("--save", help="save workspace to this .pd path after building")
    args = ap.parse_args()

    c = SimpleUDPClient(args.host, args.port)
    i = 0
    def obj(x, y, name, *a):
        nonlocal i
        c.send_message("/pd/create", [float(x), float(y), name] + list(a))
        idx = i; i += 1; return idx
    def msg(x, y, *a):
        nonlocal i
        c.send_message("/pd/msg", [float(x), float(y)] + list(a))
        idx = i; i += 1; return idx
    def con(s, o, d, n):
        c.send_message("/pd/connect", [float(s), float(o), float(d), float(n)])
    def vsl(x, y, lo, hi, label):
        return obj(x, y, "vsl", float(lo), float(hi), 0.0, 0.0, "empty", "empty",
                   label, -2.0, -8.0, 0.0, 10.0, -260098.0, -1.0, -1.0, 0.0, 1.0)
    def tgl(x, y, label):
        return obj(x, y, "tgl", 15.0, 0.0, "empty", "empty", label, 0.0, -9.0,
                   0.0, 10.0, -4034.0, -1.0, -1.0, 0.0, 1.0)

    D = args.dsp_dir
    ID = {}

    # sources -> *~ 0.4 -> dac
    ID['beat']  = obj(100,100, "faustgen~", f"{D}/beating")
    ID['rfg']   = obj(100,50,  "r", "fg")
    ID['gDrone']= obj(100,200, "*~", 0.4)
    ID['bass']  = obj(100,400, "faustgen~", f"{D}/dubbass")
    ID['rbass'] = obj(100,350, "r", "bass")
    ID['gBass'] = obj(100,500, "*~", 0.4)
    ID['gDrum'] = obj(430,760, "*~", 0.4)
    ID['dac']   = obj(200,820, "dac~")

    # clock
    ID['tgl']    = tgl(300,310, "ON")
    ID['selTgl'] = obj(300,370, "select", 0.0, 1.0)
    ID['metro']  = obj(300,430, "metro", 250.0)
    ID['mGoff']  = msg(360,340, "gate", 0.0)
    ID['mDgOff'] = msg(360,370, "gain", 0.0)
    ID['mDgOn']  = msg(360,400, "gain", 1.0)
    ID['f']      = obj(300,470, "f", 0.0)
    ID['p1']     = obj(340,500, "+", 1.0)
    ID['mod']    = obj(340,530, "%", 16.0)

    # groove router: hradio -> == -> spigot gates
    ID['gSel'] = obj(520,300, "hradio", 15.0, 1.0, 0.0, 3.0, "empty", "empty",
                     "groove", -2.0, -8.0, 0.0, 10.0, -260098.0, -1.0, -1.0, 0.0)
    ID['eq'] = [obj(520+gi*90, 340, "==", float(gi)) for gi in range(3)]
    ID['sp'] = [obj(520+gi*90, 500, "spigot") for gi in range(3)]

    # groove 0: sleng teng
    ID['s0K'] = obj(520,530, "select", 0.0, 4.0, 8.0, 12.0)
    ID['s0S'] = obj(640,530, "select", 4.0, 12.0)
    ID['s0H'] = obj(760,530, "select", 0.0,2.0,4.0,6.0,8.0,10.0,12.0,14.0)
    ID['s0B'] = obj(880,530, "select", 0.0,2.0,4.0,6.0,8.0,10.0,12.0,14.0)
    n0 = [55.0, 65.41, 82.41, 55.0, 55.0, 65.41, 82.41, 98.0]  # A1 C2 E2 ...
    ID['m0N'] = [msg(880+k*65, 560, n0[k]) for k in range(8)]
    # groove 1: steppers (D minor)
    ID['s1K'] = obj(520,600, "select", 0.0, 8.0)
    ID['s1S'] = obj(640,600, "select", 4.0, 12.0)
    ID['s1H'] = obj(760,600, "select", 2.0, 6.0, 10.0, 14.0)
    ID['s1B'] = obj(880,640, "select", 0.0, 4.0, 8.0, 12.0)
    n1 = [36.71, 55.0, 43.65, 65.41]  # D1 A1 F1 C2
    ID['m1N'] = [msg(880+k*65, 670, n1[k]) for k in range(4)]
    # groove 2: half-time dub
    ID['s2K'] = obj(520,670, "select", 0.0)
    ID['s2S'] = obj(640,670, "select", 8.0)
    ID['s2H'] = obj(760,670, "select", 4.0, 12.0)
    ID['s2B'] = obj(880,740, "select", 0.0, 6.0, 10.0)
    n2 = [55.0, 82.41, 110.0]  # A1 E2 A2
    ID['m2N'] = [msg(880+k*65, 770, n2[k]) for k in range(3)]

    # drum voices
    ID['mK']  = msg(300,590, 1.0, ",", 0.0, 120.0)
    ID['mS']  = msg(430,590, 1.0, ",", 0.0, 180.0)
    ID['mH']  = msg(560,590, 1.0, ",", 0.0, 40.0)
    ID['lK']  = obj(300,620, "line~")
    ID['lS']  = obj(430,620, "line~")
    ID['lH']  = obj(560,620, "line~")
    ID['oK']  = obj(240,650, "osc~", 55.0)
    ID['nS']  = obj(430,650, "noise~")
    ID['nH']  = obj(560,650, "noise~")
    ID['hpH'] = obj(560,680, "hip~", 8000.0)
    ID['vK']  = obj(300,680, "*~")
    ID['vS']  = obj(430,680, "*~")
    ID['vH']  = obj(560,710, "*~")

    # bass plumbing
    ID['mGon'] = msg(700,700, "gate", 1.0)
    ID['mFq']  = msg(700,730, "freq", "$1")
    ID['sBass']= obj(700,760, "s", "bass")

    # controls
    ID['sDfreq'] = vsl(1100, 50, 40, 440, "drone-freq")
    ID['sDsprd'] = vsl(1140, 50, 0, 1, "drone-spread")
    ID['sDdrif'] = vsl(1180, 50, 0.01, 1, "drone-drift")
    ID['mDfreq'] = msg(1100, 210, "freq", "$1")
    ID['mDsprd'] = msg(1140, 210, "spread", "$1")
    ID['mDdrif'] = msg(1180, 210, "drift", "$1")
    ID['sfg']    = obj(1140, 240, "s", "fg")
    ID['sBcut']  = vsl(1260, 50, 80, 4000, "cutoff")
    ID['sBres']  = vsl(1300, 50, 0, 1.5, "res")
    ID['sBgn']   = vsl(1340, 50, 0, 1, "bass-gain")
    ID['sLfoR']  = vsl(1380, 50, 0.02, 20, "lfo-rate")
    ID['sLfoD']  = vsl(1420, 50, 0, 1, "lfo-depth")
    ID['mBcut']  = msg(1260, 210, "cutoff", "$1")
    ID['mBres']  = msg(1300, 210, "res", "$1")
    ID['mBgn']   = msg(1340, 210, "gain", "$1")
    ID['mLfoR']  = msg(1380, 210, "lfoRate", "$1")
    ID['mLfoD']  = msg(1420, 210, "lfoDepth", "$1")
    ID['selShape'] = obj(1300, 260, "hradio", 15.0, 1.0, 0.0, 5.0, "empty",
                         "empty", "lfo-shape", -2.0, -8.0, 0.0, 10.0,
                         -260098.0, -1.0, -1.0, 0.0)
    ID['mShape'] = msg(1300, 320, "lfoShape", "$1")
    ID['sTmp']   = obj(1100, 340, "nbx", 5.0, 14.0, 80.0, 1000.0, 0.0, 0.0,
                       "empty", "empty", "tempo-ms", -2.0, 0.0, 10.0,
                       -260098.0, -1.0, -1.0, 250.0, 256.0)

    g = lambda k: ID[k]
    # audio
    con(g('rfg'),0,g('beat'),0); con(g('beat'),0,g('gDrone'),0)
    con(g('gDrone'),0,g('dac'),0); con(g('gDrone'),0,g('dac'),1)
    con(g('rbass'),0,g('bass'),0); con(g('bass'),0,g('gBass'),0)
    con(g('gBass'),0,g('dac'),0); con(g('gBass'),0,g('dac'),1)
    con(g('vK'),0,g('gDrum'),0); con(g('vS'),0,g('gDrum'),0); con(g('vH'),0,g('gDrum'),0)
    con(g('gDrum'),0,g('dac'),0); con(g('gDrum'),0,g('dac'),1)
    # clock
    con(g('tgl'),0,g('metro'),0); con(g('tgl'),0,g('selTgl'),0)
    con(g('selTgl'),0,g('mGoff'),0);  con(g('mGoff'),0,g('sBass'),0)
    con(g('selTgl'),0,g('mDgOff'),0); con(g('mDgOff'),0,g('sfg'),0)
    con(g('selTgl'),1,g('mDgOn'),0);  con(g('mDgOn'),0,g('sfg'),0)
    con(g('metro'),0,g('f'),0); con(g('f'),0,g('p1'),0)
    con(g('p1'),0,g('mod'),0); con(g('mod'),0,g('f'),1)
    con(g('sTmp'),0,g('metro'),1)
    # groove router
    for gi in range(3):
        con(g('gSel'),0,ID['eq'][gi],0); con(ID['eq'][gi],0,ID['sp'][gi],1)
        con(g('f'),0,ID['sp'][gi],0)
    grooves = [('s0K','s0S','s0H','s0B'),('s1K','s1S','s1H','s1B'),('s2K','s2S','s2H','s2B')]
    for gi, ks in enumerate(grooves):
        for k in ks: con(ID['sp'][gi], 0, g(k), 0)
    # drums
    for o in range(4): con(g('s0K'),o,g('mK'),0)
    for o in range(2): con(g('s0S'),o,g('mS'),0)
    for o in range(8): con(g('s0H'),o,g('mH'),0)
    for o in range(2): con(g('s1K'),o,g('mK'),0)
    for o in range(2): con(g('s1S'),o,g('mS'),0)
    for o in range(4): con(g('s1H'),o,g('mH'),0)
    con(g('s2K'),0,g('mK'),0); con(g('s2S'),0,g('mS'),0)
    for o in range(2): con(g('s2H'),o,g('mH'),0)
    con(g('mK'),0,g('lK'),0); con(g('mS'),0,g('lS'),0); con(g('mH'),0,g('lH'),0)
    con(g('oK'),0,g('vK'),0); con(g('lK'),0,g('vK'),1)
    con(g('nS'),0,g('vS'),0); con(g('lS'),0,g('vS'),1)
    con(g('nH'),0,g('hpH'),0); con(g('hpH'),0,g('vH'),0); con(g('lH'),0,g('vH'),1)
    # bass seq
    for k,idx in enumerate(ID['m0N']):
        con(g('s0B'),k,idx,0); con(idx,0,g('mFq'),0); con(g('s0B'),k,g('mGon'),0)
    for k,idx in enumerate(ID['m1N']):
        con(g('s1B'),k,idx,0); con(idx,0,g('mFq'),0); con(g('s1B'),k,g('mGon'),0)
    for k,idx in enumerate(ID['m2N']):
        con(g('s2B'),k,idx,0); con(idx,0,g('mFq'),0); con(g('s2B'),k,g('mGon'),0)
    con(g('mFq'),0,g('sBass'),0); con(g('mGon'),0,g('sBass'),0)
    # controls
    con(g('sDfreq'),0,g('mDfreq'),0); con(g('mDfreq'),0,g('sfg'),0)
    con(g('sDsprd'),0,g('mDsprd'),0); con(g('mDsprd'),0,g('sfg'),0)
    con(g('sDdrif'),0,g('mDdrif'),0); con(g('mDdrif'),0,g('sfg'),0)
    con(g('sBcut'),0,g('mBcut'),0); con(g('mBcut'),0,g('sBass'),0)
    con(g('sBres'),0,g('mBres'),0); con(g('mBres'),0,g('sBass'),0)
    con(g('sBgn'),0,g('mBgn'),0);   con(g('mBgn'),0,g('sBass'),0)
    con(g('sLfoR'),0,g('mLfoR'),0); con(g('mLfoR'),0,g('sBass'),0)
    con(g('sLfoD'),0,g('mLfoD'),0); con(g('mLfoD'),0,g('sBass'),0)
    con(g('selShape'),0,g('mShape'),0); con(g('mShape'),0,g('sBass'),0)

    print(f"built {i} objects")
    if args.save:
        c.send_message("/pd/save", [args.save])
        print(f"saved workspace to {args.save}")

if __name__ == "__main__":
    main()

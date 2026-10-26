/* gbc-music piano roll: an animated, zoomable canvas piano roll whose playhead follows the audio clip it is bound to.
 * Inline this file in a page. Data: the JSON written by `compose.py events`
 * (see docs/PIANOROLL.md). API: window.GbcPianoRoll.create(container, data, opts) -> roll.
 *
 *   opts.audio   <audio> element the roll is bound to; the playhead = audio.currentTime - opts.offset
 *   opts.offset  seconds into the audio at which music frame 0 (music_init) sounds (default data.offset_s or 0)
 *   opts.range   [start, end] in audio seconds: the roll shows that slice of a longer recording (range players)
 *   opts.clock   function () -> music seconds (or null): a clock-bound roll (lockstep emulator cores); no seeking
 *   opts.height  canvas height in CSS px (default 240), opts.follow (default true), opts.seek (default true),
 *   opts.sections [{label, start_bar, bars}] section labels on the ruler (0-based bars), opts.title (toolbar text)
 *
 *   roll.bind(audio, {offset, range}) roll.bindClock(fn) roll.setRange([s, e] | null) roll.fit() roll.fitAll()
 *   roll.zoom(factor[, anchorSec]) roll.pan(seconds) roll.setFollow(bool) roll.seek(musicSec) roll.time()
 *   roll.state() roll.redraw() roll.destroy()        GbcPianoRoll.mountAll([root]) for data-pianoroll figures.
 *
 * Colours are CSS custom properties read from the container (fallbacks in TOKENS): --pr-pulse1 --pr-pulse2 --pr-wave
 * --pr-noise --pr-bg --pr-grid --pr-grid-strong --pr-ink --pr-muted --pr-playhead --pr-lit --pr-panel --pr-line.
 * Redraws only on requestAnimationFrame while its clip plays or while the user interacts; one roll per clip animates.
 * prefers-reduced-motion keeps the playhead but drops the glow. devicePixelRatio aware.
 * Panned songs (notes with `pan` -1 / 1 / "LR", a top-level `pan_changes` list): a note on one side carries a bright
 * wedge on that edge (left edge = left, right edge = right; both for an auto-pan) and a thin L / R strip above the
 * noise lane shows each pulse channel's side over time; a song without pans draws exactly as before. */
(function (global) {
  'use strict';
  var FPS = 4194304 / 70224;
  var CH = ['pulse 1', 'pulse 2', 'wave', 'noise'];
  var TOKENS = {
    pulse1: ['--pr-pulse1', '#3f86e6'], pulse2: ['--pr-pulse2', '#e67b2c'], wave: ['--pr-wave', '#1fa874'], noise: ['--pr-noise', '#9b87c9'],
    bg: ['--pr-bg', '#15161a'], grid: ['--pr-grid', 'rgba(255,255,255,0.07)'], gridStrong: ['--pr-grid-strong', 'rgba(255,255,255,0.22)'],
    ink: ['--pr-ink', '#e9e9e4'], muted: ['--pr-muted', 'rgba(233,233,228,0.6)'], playhead: ['--pr-playhead', '#ff4d5e'],
    lit: ['--pr-lit', '#ffffff'], key: ['--pr-key', 'rgba(255,255,255,0.035)'], panel: ['--pr-panel', 'transparent'], line: ['--pr-line', 'rgba(127,127,127,0.35)']
  };
  var NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  var BLACK = { 1: 1, 3: 1, 6: 1, 8: 1, 10: 1 };
  var GUTTER = 36, RULER = 20, NOISE_H = 34, PAD_R = 8, PAN_H = 14;
  var reduced = global.matchMedia ? global.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var css = '.pr-root{position:relative;font:12px/1.3 system-ui,sans-serif;color:var(--pr-ink,#e9e9e4);background:var(--pr-panel,transparent);border-radius:8px;overflow:hidden}' +
    '.pr-bar{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 8px;background:var(--pr-bg,#15161a);border-bottom:1px solid var(--pr-line,rgba(127,127,127,.35))}' +
    '.pr-bar .pr-title{font-weight:600;margin-right:auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
    '.pr-bar .pr-pos{font-variant-numeric:tabular-nums;color:var(--pr-muted,rgba(233,233,228,.6));white-space:nowrap}' +
    '.pr-bar button{font:inherit;color:inherit;background:transparent;border:1px solid var(--pr-line,rgba(127,127,127,.35));border-radius:6px;padding:2px 8px;cursor:pointer;min-width:28px;min-height:26px}' +
    '.pr-bar button[aria-pressed="true"]{background:var(--pr-playhead,#ff4d5e);color:#fff;border-color:transparent}' +
    '.pr-bar button:focus-visible{outline:2px solid var(--pr-playhead,#ff4d5e);outline-offset:1px}' +
    '.pr-root .pr-canvas{display:block;width:100%;max-width:none;aspect-ratio:auto;image-rendering:auto;border-radius:0;border:0;justify-self:stretch;touch-action:pan-y;cursor:crosshair;outline:none;background:var(--pr-bg,#15161a)}' +   /* beats a page-wide `canvas {}` rule (the duet page styles its screens) */
    '.pr-canvas:focus-visible{box-shadow:inset 0 0 0 2px var(--pr-playhead,#ff4d5e)}' +
    '.pr-legend{display:flex;flex-wrap:wrap;gap:4px 12px;padding:4px 8px 6px;background:var(--pr-bg,#15161a);color:var(--pr-muted,rgba(233,233,228,.6));font-size:11px}' +
    '.pr-legend i{display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:-1px;margin-right:4px}' +
    '.pr-hidden{display:none!important}';
  var styled = false;
  function ensureStyle(doc) {
    if (styled) return;
    var s = doc.createElement('style'); s.setAttribute('data-pianoroll-style', ''); s.textContent = css; doc.head.appendChild(s); styled = true;
  }
  function el(doc, tag, cls, text) { var e = doc.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function noteName(m) { return NAMES[((m % 12) + 12) % 12] + (Math.floor(m / 12) - 1); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function alphaOf(color, a) {   // apply an alpha to a css colour (hex or rgb[a])
    var m;
    if ((m = /^#([0-9a-f]{3,8})$/i.exec(color))) {
      var h = m[1]; if (h.length === 3 || h.length === 4) h = h.split('').map(function (c) { return c + c; }).join('');
      return 'rgba(' + parseInt(h.slice(0, 2), 16) + ',' + parseInt(h.slice(2, 4), 16) + ',' + parseInt(h.slice(4, 6), 16) + ',' + a + ')';
    }
    if ((m = /^rgba?\(([^)]+)\)$/i.exec(color))) { var p = m[1].split(',').slice(0, 3).map(function (x) { return x.trim(); }); return 'rgba(' + p.join(',') + ',' + a + ')'; }
    return color;
  }

  function Roll(container, data, opts) {
    var self = this;
    opts = opts || {};
    this.doc = container.ownerDocument;
    ensureStyle(this.doc);
    this.container = container;
    this.data = data;
    this.notes = (data.notes || []).slice().sort(function (a, b) { return a.t - b.t; });
    this.fps = data.fps || FPS;
    this.fpr = data.frames_per_row || 6;
    this.rows = data.rows_per_bar || 16;
    this.rowsPerBeat = data.rows_per_beat || 4;
    this.bars = data.bars || 1;
    this.secPerRow = this.fpr / this.fps;
    this.secPerBar = this.rows * this.secPerRow;
    this.length = data.length_s || this.bars * this.secPerBar;
    this.loopBar = data.loop_bar || 0;
    this.loopS = this.loopBar * this.secPerBar;
    this.sections = opts.sections || (data.songs && data.songs.length > 1 ? data.songs.map(function (s) { return { label: s.title || s.name, start_bar: s.start_bar, bars: s.bars }; }) : []);
    this.offset = opts.offset != null ? +opts.offset : (data.offset_s || 0);
    this.follow = opts.follow !== false;
    this.canSeek = opts.seek !== false;
    this.height = opts.height || 240;
    this.audio = null; this.clock = null; this.range = null;
    this.view = { start: 0, span: this.length };
    this.lastTime = null; this.hover = null; this.raf = 0; this.playing = false; this.interactUntil = 0; this.destroyed = false;
    this.lastCt = -1; this.lastWall = 0; this.drawnTime = null;
    // pitch extent of the tonal channels (arp intervals, bends and pitch envelopes included)
    var lo = 127, hi = 0, n, i;
    for (i = 0; i < this.notes.length; i++) {
      n = this.notes[i]; if (n.ch === 3) continue;
      var a = n.midi, b = n.midi;
      if (n.arp) b = Math.max(b, n.midi + Math.max.apply(null, n.arp.filter(function (x) { return x < 255; })));
      if (n.trill) b = Math.max(b, n.midi + n.trill); if (n.mordent) b = Math.max(b, n.midi + n.mordent);
      if (n.bend) { a = Math.min(a, n.midi + n.bend[0]); b = Math.max(b, n.midi + n.bend[0]); }
      if (n.penv) b = Math.max(b, n.midi + n.penv[0]);
      if (n.porta_from != null) { a = Math.min(a, n.porta_from); b = Math.max(b, n.porta_from); }
      lo = Math.min(lo, a); hi = Math.max(hi, b);
    }
    if (lo > hi) { lo = 48; hi = 84; }
    this.pLo = Math.max(0, lo - 2); this.pHi = Math.min(127, hi + 2);
    // noise pseudo-pitch extent
    var nlo = 127, nhi = 0;
    for (i = 0; i < this.notes.length; i++) { n = this.notes[i]; if (n.ch !== 3) continue; nlo = Math.min(nlo, n.midi); nhi = Math.max(nhi, n.midi); }
    this.nLo = nlo > nhi ? 60 : nlo - 1; this.nHi = nlo > nhi ? 100 : nhi + 1;
    // pans: per pulse channel a list of [musicSeconds, side] (-1 left, 0 centre, 1 right); the strip only exists when the song pans
    this.pans = [[], []];
    var pc = data.pan_changes || [];
    for (i = 0; i < pc.length; i++) if (pc[i].ch < 2) this.pans[pc[i].ch].push([(pc[i].f || 0) / this.fps, pc[i].pan]);
    this.hasPan = pc.length > 0 || this.notes.some(function (x) { return x.pan != null; });

    // DOM
    var root = this.root = el(this.doc, 'div', 'pr-root');
    root.setAttribute('role', 'group'); root.setAttribute('aria-label', 'piano roll' + (opts.title ? ': ' + opts.title : ''));
    var bar = this.bar = el(this.doc, 'div', 'pr-bar');
    bar.appendChild(el(this.doc, 'span', 'pr-title', opts.title || data.title || data.song || 'piano roll'));
    this.posEl = el(this.doc, 'span', 'pr-pos', '');
    bar.appendChild(this.posEl);
    var mk = function (label, title, fn) { var b = el(self.doc, 'button', null, label); b.type = 'button'; b.title = title; b.setAttribute('aria-label', title); b.addEventListener('click', function () { fn(); self.canvas.focus({ preventScroll: true }); }); bar.appendChild(b); return b; };
    mk('−', 'zoom out (also: - key, wheel)', function () { self.zoom(1 / 1.5); });
    mk('+', 'zoom in (also: + key, wheel, pinch)', function () { self.zoom(1.5); });
    this.fitBtn = mk('fit', 'fit the clip (0 key)', function () { self.fit(); });
    this.allBtn = mk('all', 'show the whole song', function () { self.fitAll(); });
    this.allBtn.classList.add('pr-hidden');
    this.followBtn = mk('follow', 'keep the playhead in view while playing (f key)', function () { self.setFollow(!self.follow); });
    this.followBtn.setAttribute('aria-pressed', String(this.follow));
    root.appendChild(bar);
    var canvas = this.canvas = el(this.doc, 'canvas', 'pr-canvas');
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', 'piano roll canvas: drag to pan, wheel or pinch to zoom, click to seek');
    canvas.style.height = this.height + 'px';
    root.appendChild(canvas);
    var legend = el(this.doc, 'div', 'pr-legend');
    legend.appendChild(this.legendItem('pulse1', 'pulse 1')); legend.appendChild(this.legendItem('pulse2', 'pulse 2'));
    legend.appendChild(this.legendItem('wave', 'wave')); legend.appendChild(this.legendItem('noise', 'noise'));
    legend.appendChild(el(this.doc, 'span', null, 'bars on the ruler, seconds on hover; faded tail = envelope has died while the key is held' + (this.hasPan ? '; bright edge = note panned to that side, L / R strip = each pulse channel\u2019s side' : '')));
    root.appendChild(legend);
    // hide static fallbacks (the probe PNG) once the live roll exists
    var fb = container.querySelectorAll('.pr-fallback, img');
    for (i = 0; i < fb.length; i++) fb[i].classList.add('pr-hidden');
    container.appendChild(root);
    this.ctx = canvas.getContext('2d');
    this.readColors();
    this.bindEvents();
    if (opts.clock) this.bindClock(opts.clock);
    else if (opts.audio) this.bind(opts.audio, { offset: this.offset, range: opts.range });
    else this.fitAll();
    this.resize();
  }

  Roll.prototype.legendItem = function (tok, label) {
    var s = el(this.doc, 'span'), i = el(this.doc, 'i');
    i.style.background = 'var(' + TOKENS[tok][0] + ',' + TOKENS[tok][1] + ')';
    s.appendChild(i); s.appendChild(this.doc.createTextNode(label)); return s;
  };
  Roll.prototype.readColors = function () {
    var cs = global.getComputedStyle(this.container), c = this.colors = {};
    for (var k in TOKENS) { var v = cs.getPropertyValue(TOKENS[k][0]).trim(); c[k] = v || TOKENS[k][1]; }
    c.ch = [c.pulse1, c.pulse2, c.wave, c.noise];
  };

  // ---- time -----------------------------------------------------------------------------------------------------
  Roll.prototype.clipStart = function () { return this.range ? this.range[0] - this.offset : 0; };           // music seconds
  Roll.prototype.clipEnd = function () { return this.range ? this.range[1] - this.offset : this.length; };
  Roll.prototype.wrapLoop = function (t) {
    if (t == null) return null;
    if (t > this.length && this.length > this.loopS) t = this.loopS + ((t - this.length) % (this.length - this.loopS));
    return t;
  };
  Roll.prototype.time = function () {                      // current music time, or null when nothing is bound
    if (this.clock) { var v = this.clock(); return v == null ? null : this.wrapLoop(v); }
    if (!this.audio) return null;
    var a = this.audio, ct = a.currentTime, now = global.performance ? performance.now() : Date.now(), est = ct;
    if (ct !== this.lastCt) { this.lastCt = ct; this.lastWall = now; }
    else if (!a.paused && !a.ended) est = ct + (now - this.lastWall) / 1000 * (a.playbackRate || 1);
    if (this.range && (est < this.range[0] - 0.05 || est > this.range[1] + 0.05)) return null;   // another clip of the same recording is playing
    return this.wrapLoop(est - this.offset);
  };
  Roll.prototype.state = function () {
    return { time: this.time(), drawnTime: this.drawnTime, viewStart: this.view.start, viewSpan: this.view.span, follow: this.follow, playing: this.playing, offset: this.offset, range: this.range, clipStart: this.clipStart(), clipEnd: this.clipEnd() };
  };

  // ---- binding --------------------------------------------------------------------------------------------------
  Roll.prototype.bind = function (audio, o) {
    var self = this;
    this.unbind();
    o = o || {};
    this.audio = audio;
    if (o.offset != null) this.offset = +o.offset;
    this.range = o.range || null;
    this.allBtn.classList.toggle('pr-hidden', !this.range);
    var onPlay = function () { self.setPlaying(true); }, onStop = function () { self.setPlaying(false); self.invalidate(); };
    var onSeek = function () { self.lastCt = -1; self.invalidate(); };
    audio.addEventListener('play', onPlay); audio.addEventListener('playing', onPlay);
    audio.addEventListener('pause', onStop); audio.addEventListener('ended', onStop);
    audio.addEventListener('seeked', onSeek); audio.addEventListener('timeupdate', onSeek);
    this.unbindFns = [function () { audio.removeEventListener('play', onPlay); audio.removeEventListener('playing', onPlay); audio.removeEventListener('pause', onStop); audio.removeEventListener('ended', onStop); audio.removeEventListener('seeked', onSeek); audio.removeEventListener('timeupdate', onSeek); }];
    this.fit();
    if (!audio.paused && !audio.ended) this.setPlaying(true);
  };
  Roll.prototype.bindClock = function (fn) {
    this.unbind();
    this.clock = fn; this.canSeek = false;
    this.fitAll();
    this.setPlaying(true);     // the loop runs while the clock moves; redraws only when the time changes
  };
  Roll.prototype.unbind = function () {
    if (this.unbindFns) { this.unbindFns.forEach(function (f) { f(); }); this.unbindFns = null; }
    this.audio = null; this.clock = null; this.setPlaying(false);
  };
  Roll.prototype.setRange = function (range, opts) {
    this.range = range ? [+range[0], +range[1]] : null;
    this.allBtn.classList.toggle('pr-hidden', !this.range);
    this.lastCt = -1;
    if (!opts || opts.fit !== false) this.fit(); else this.invalidate();
  };

  // ---- view -----------------------------------------------------------------------------------------------------
  Roll.prototype.innerW = function () { return Math.max(40, this.cssW - GUTTER - PAD_R); };
  Roll.prototype.xOf = function (t) { return GUTTER + (t - this.view.start) / this.view.span * this.innerW(); };
  Roll.prototype.tOf = function (x) { return this.view.start + (x - GUTTER) / this.innerW() * this.view.span; };
  Roll.prototype.clampView = function () {
    var lo = Math.min(0, this.clipStart()), hi = Math.max(this.length, this.clipEnd());
    var minSpan = Math.min(0.25, hi - lo);
    this.view.span = clamp(this.view.span, minSpan, hi - lo);
    this.view.start = clamp(this.view.start, lo, hi - this.view.span);
  };
  Roll.prototype.setView = function (start, span) { this.view.start = start; this.view.span = span; this.clampView(); this.invalidate(); };
  Roll.prototype.fit = function () { var s = this.clipStart(), e = this.clipEnd(); this.setView(s, Math.max(0.25, e - s)); };
  Roll.prototype.fitAll = function () { this.setView(0, this.length); };
  Roll.prototype.zoom = function (factor, anchor) {
    if (anchor == null) { var t = this.time(); anchor = (t != null && t >= this.view.start && t <= this.view.start + this.view.span) ? t : this.view.start + this.view.span / 2; }
    var frac = (anchor - this.view.start) / this.view.span;
    var span = this.view.span / factor;
    this.setView(anchor - frac * span, span);
    this.touch();
  };
  Roll.prototype.pan = function (dt) { this.setView(this.view.start + dt, this.view.span); this.touch(); };
  Roll.prototype.setFollow = function (on) { this.follow = !!on; this.followBtn.setAttribute('aria-pressed', String(this.follow)); this.invalidate(); };
  Roll.prototype.seek = function (t) {
    if (!this.audio || !this.canSeek) return;
    var lo = this.clipStart(), hi = this.clipEnd();
    t = clamp(t, lo, Math.max(lo, hi - 0.01));
    try { this.audio.currentTime = this.offset + t; } catch (e) { /* not seekable yet */ }
    this.lastCt = -1; this.invalidate();
  };
  Roll.prototype.touch = function () {   // user interaction: animate briefly
    this.interactUntil = (global.performance ? performance.now() : Date.now()) + 250;
    this.loop();
  };
  Roll.prototype.invalidate = function () { this.dirty = true; this.loop(); };
  Roll.prototype.setPlaying = function (p) { this.playing = !!p; if (p) this.loop(); else this.invalidate(); };
  Roll.prototype.loop = function () {
    var self = this;
    if (this.raf || this.destroyed) return;
    this.raf = global.requestAnimationFrame(function step() {
      self.raf = 0;
      if (self.destroyed) return;
      var now = global.performance ? performance.now() : Date.now();
      var t = self.time();
      var moving = self.playing && t !== self.drawnTime;
      if (self.dirty || moving || now < self.interactUntil) { self.draw(t); self.dirty = false; }
      if (self.playing || now < self.interactUntil) self.raf = global.requestAnimationFrame(step);
    });
  };

  // ---- events ---------------------------------------------------------------------------------------------------
  Roll.prototype.bindEvents = function () {
    var self = this, c = this.canvas, drag = null, pinch = null, pointers = {};
    this.ro = global.ResizeObserver ? new ResizeObserver(function () { self.resize(); }) : null;
    if (this.ro) this.ro.observe(this.root);
    this.onMedia = function () { self.readColors(); self.invalidate(); };
    this.mql = global.matchMedia ? global.matchMedia('(prefers-color-scheme: dark)') : null;
    if (this.mql && this.mql.addEventListener) this.mql.addEventListener('change', this.onMedia);
    this.mo = global.MutationObserver ? new MutationObserver(this.onMedia) : null;
    if (this.mo) this.mo.observe(this.doc.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class', 'style'] });
    c.addEventListener('pointerdown', function (e) {
      pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
      var ids = Object.keys(pointers);
      if (ids.length === 2) { var p = ids.map(function (k) { return pointers[k]; }); pinch = { d: Math.abs(p[0].x - p[1].x) || 1, span: self.view.span, mid: self.tOf(((p[0].x + p[1].x) / 2) - c.getBoundingClientRect().left) }; drag = null; return; }
      drag = { x: e.clientX, start: self.view.start, moved: false, id: e.pointerId };
      try { c.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      c.focus({ preventScroll: true });
    });
    c.addEventListener('pointermove', function (e) {
      var r = c.getBoundingClientRect();
      if (pointers[e.pointerId]) { pointers[e.pointerId].x = e.clientX; pointers[e.pointerId].y = e.clientY; }
      if (pinch) {
        var p = Object.keys(pointers).map(function (k) { return pointers[k]; });
        if (p.length === 2) { var d = Math.abs(p[0].x - p[1].x) || 1; var span = pinch.span * pinch.d / d; var frac = (pinch.mid - self.view.start) / self.view.span; self.setView(pinch.mid - frac * span, span); self.touch(); }
        return;
      }
      if (drag && e.pointerId === drag.id) {
        var dx = e.clientX - drag.x;
        if (Math.abs(dx) > 3) drag.moved = true;
        if (drag.moved) { self.follow && self.playing && self.setFollow(false); self.setView(drag.start - dx / self.innerW() * self.view.span, self.view.span); self.touch(); }
      }
      self.hover = { x: e.clientX - r.left, y: e.clientY - r.top };
      self.updatePos(); if (!self.playing) self.invalidate();
    });
    var up = function (e) {
      delete pointers[e.pointerId];
      if (pinch && Object.keys(pointers).length < 2) pinch = null;
      if (drag && e.pointerId === drag.id) {
        if (!drag.moved && self.canSeek && self.audio) { var r = c.getBoundingClientRect(); var x = e.clientX - r.left; if (x >= GUTTER) self.seek(self.tOf(x)); }
        drag = null;
      }
    };
    c.addEventListener('pointerup', up); c.addEventListener('pointercancel', up);
    c.addEventListener('pointerleave', function () { self.hover = null; self.updatePos(); if (!self.playing) self.invalidate(); });
    c.addEventListener('wheel', function (e) {
      var r = c.getBoundingClientRect(), x = e.clientX - r.left;
      if (e.shiftKey || (Math.abs(e.deltaX) > Math.abs(e.deltaY))) {   // horizontal: pan
        var d = (e.shiftKey ? e.deltaY : e.deltaX) || e.deltaX;
        e.preventDefault(); self.follow && self.playing && self.setFollow(false); self.pan(d / self.innerW() * self.view.span * 1.5); return;
      }
      if (e.ctrlKey || e.metaKey || self.doc.activeElement === c) {   // pinch gesture or a focused roll: zoom at the cursor
        e.preventDefault();
        var f = Math.pow(1.0015, -e.deltaY * (e.ctrlKey ? 8 : 1));
        self.zoom(f, self.tOf(Math.max(GUTTER, x)));
      }
    }, { passive: false });
    c.addEventListener('keydown', function (e) {
      var k = e.key;
      if (k === '+' || k === '=') self.zoom(1.5); else if (k === '-' || k === '_') self.zoom(1 / 1.5);
      else if (k === '0') self.fit(); else if (k === 'f' || k === 'F') self.setFollow(!self.follow);
      else if (k === 'ArrowLeft') { self.setFollow(false); self.pan(-self.view.span * 0.1); } else if (k === 'ArrowRight') { self.setFollow(false); self.pan(self.view.span * 0.1); }
      else if (k === 'Home') self.pan(-1e9); else if (k === 'End') self.pan(1e9);
      else return;
      e.preventDefault();
    });
    c.addEventListener('dblclick', function (e) { e.preventDefault(); self.fit(); });
  };
  Roll.prototype.updatePos = function () {
    var t = this.time(), txt = '';
    if (this.hover && this.hover.x >= GUTTER) {
      var ht = this.tOf(this.hover.x);
      txt = this.barRow(ht) + ' · ' + (ht + this.offset).toFixed(2) + ' s';
      var n = this.noteAt(this.hover.x, this.hover.y);
      if (n) txt += ' · ' + this.describe(n);
    } else if (t != null) txt = this.barRow(t) + ' · ' + (t + this.offset).toFixed(2) + ' s';
    if (txt !== this.posTxt) { this.posTxt = txt; this.posEl.textContent = txt; }
  };
  Roll.prototype.barRow = function (t) {
    var bar = Math.floor(t / this.secPerBar), row = Math.floor((t - bar * this.secPerBar) / this.secPerRow);
    return 'bar ' + (bar + 1) + '.' + (clamp(row, 0, this.rows - 1) + 1);
  };
  Roll.prototype.describe = function (n) {
    var s = CH[n.ch] + ' ' + (n.ch === 3 ? ('drum ' + (n.drum || '?')) : noteName(n.midi)) + (n.inst && n.ch !== 3 ? ' @' + n.inst : '') + ' v' + n.vol;
    if (n.arp) s += ' arp[' + n.arp.filter(function (x) { return x < 255; }).join(' ') + ']/' + n.arp_f + 'f';
    if (n.trill) s += ' trill ' + n.trill; if (n.mordent) s += ' mordent ' + n.mordent;
    if (n.bend) s += ' bend ' + n.bend[0] + ' in ' + n.bend[1] + 'f'; if (n.porta) s += ' porta ' + n.porta + 'f';
    if (n.slide) s += ' slide ' + n.slide; if (n.vib) s += ' vib ' + n.vib.join(','); if (n.trem) s += ' trem ' + n.trem.join(',');
    if (n.penv) s += ' penv +' + n.penv[0] + '/' + n.penv[1] + 'f'; if (n.cut) s += ' cut ' + n.cut + 'f'; if (n.echo) s += ' (echo)'; if (n.split) s += ' (32nd)';
    if (n.pan === -1) s += ' pan L'; else if (n.pan === 1) s += ' pan R'; else if (n.pan === 'LR') s += ' auto-pan L/R every ' + n.pan_f + 'f';
    return s;
  };
  Roll.prototype.noteAt = function (x, y) {
    var t = this.tOf(x), g = this.geom(), best = null;
    for (var i = 0; i < this.notes.length; i++) {
      var n = this.notes[i];
      if (n.t > t) break;
      if (t > n.t + Math.max(n.d, 2 / this.innerW() * this.view.span)) continue;
      var ny = n.ch === 3 ? g.noiseY(n.midi) : g.pitchY(n.midi) + g.rowH / 2;
      if (Math.abs(ny - y) <= Math.max(4, g.rowH / 2 + 1)) best = n;
    }
    return best;
  };

  // ---- drawing --------------------------------------------------------------------------------------------------
  Roll.prototype.resize = function () {
    var dpr = global.devicePixelRatio || 1, w = this.root.clientWidth || 600;
    this.cssW = w; this.cssH = this.height;
    this.canvas.width = Math.round(w * dpr); this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.width = w + 'px';
    this.dpr = dpr;
    this.clampView();
    this.invalidate();
  };
  Roll.prototype.geom = function () {
    var self = this, top = RULER + 4, noiseTop = this.cssH - NOISE_H, panTop = noiseTop - (this.hasPan ? PAN_H : 0), h = panTop - top - 6;
    var nRows = this.pHi - this.pLo + 1, rowH = h / nRows;
    return { top: top, rowH: rowH, noiseTop: noiseTop, panTop: panTop, h: h,
      pitchY: function (m) { return top + (self.pHi - m) * rowH; },
      noiseY: function (m) { return noiseTop + 6 + (self.nHi - m) / Math.max(1, self.nHi - self.nLo) * (NOISE_H - 12); } };
  };
  Roll.prototype.draw = function (t) {
    var ctx = this.ctx, C = this.colors, W = this.cssW, H = this.cssH, g = this.geom(), self = this;
    if (!ctx || !W) return;
    if (this.follow && this.playing && t != null) {   // page the view when the playhead leaves it; never past a clip's end
      var vEnd = this.view.start + this.view.span, atClipEnd = this.range && vEnd >= this.clipEnd() - 1e-6;
      if (t < this.view.start || (t > vEnd && !atClipEnd)) { this.view.start = t - this.view.span * 0.1; this.clampView(); }
    }
    this.drawnTime = t;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
    var v = this.view, x0 = GUTTER, x1 = W - PAD_R, pxPerSec = this.innerW() / v.span;
    var tA = v.start, tB = v.start + v.span;
    // key shading + octave lines
    ctx.save(); ctx.beginPath(); ctx.rect(x0, RULER, x1 - x0, H - RULER); ctx.clip();
    if (g.rowH >= 2.5) {
      ctx.fillStyle = C.key;
      for (var m = this.pLo; m <= this.pHi; m++) if (BLACK[m % 12]) ctx.fillRect(x0, g.pitchY(m), x1 - x0, g.rowH);
    }
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1; ctx.beginPath();
    for (m = this.pLo; m <= this.pHi; m++) if (m % 12 === 0) { var yy = Math.round(g.pitchY(m) + g.rowH) + 0.5; ctx.moveTo(x0, yy); ctx.lineTo(x1, yy); }
    ctx.stroke();
    // noise strip separator (and the pan strip above it when the song pans)
    ctx.strokeStyle = C.gridStrong; ctx.beginPath(); ctx.moveTo(x0, g.noiseTop + 0.5); ctx.lineTo(x1, g.noiseTop + 0.5); ctx.stroke();
    if (this.hasPan) this.drawPanStrip(ctx, g, x0, x1, tA, tB);
    // bar / beat / row lines
    var pxPerBar = this.secPerBar * pxPerSec, pxPerRow = this.secPerRow * pxPerSec;
    var b0 = Math.max(0, Math.floor(tA / this.secPerBar)), b1 = Math.min(this.bars, Math.ceil(tB / this.secPerBar));
    ctx.beginPath(); ctx.strokeStyle = C.grid;
    if (pxPerRow >= 7) for (var b = b0; b < b1; b++) for (var r = 1; r < this.rows; r++) { if (r % this.rowsPerBeat === 0 && pxPerBar >= 24) continue; var xr = Math.round(this.xOf(b * this.secPerBar + r * this.secPerRow)) + 0.5; ctx.moveTo(xr, RULER); ctx.lineTo(xr, g.noiseTop); }
    ctx.stroke();
    if (pxPerBar >= 24) { ctx.beginPath(); ctx.strokeStyle = C.gridStrong; ctx.globalAlpha = 0.6;
      for (b = b0; b < b1; b++) for (r = this.rowsPerBeat; r < this.rows; r += this.rowsPerBeat) { var xb = Math.round(this.xOf(b * this.secPerBar + r * this.secPerRow)) + 0.5; ctx.moveTo(xb, RULER); ctx.lineTo(xb, H); }
      ctx.stroke(); ctx.globalAlpha = 1; }
    ctx.beginPath(); ctx.strokeStyle = C.gridStrong;
    var barStep = pxPerBar >= 6 ? 1 : pxPerBar >= 1.5 ? 4 : 8;
    for (b = b0; b <= b1; b++) if (b % barStep === 0) { var xx = Math.round(this.xOf(b * this.secPerBar)) + 0.5; ctx.moveTo(xx, RULER); ctx.lineTo(xx, H); }
    ctx.stroke();
    // loop point
    if (this.loopS > 0) { ctx.save(); ctx.setLineDash([3, 3]); ctx.strokeStyle = C.playhead; ctx.globalAlpha = 0.7; var xl = Math.round(this.xOf(this.loopS)) + 0.5; ctx.beginPath(); ctx.moveTo(xl, RULER); ctx.lineTo(xl, H); ctx.stroke(); ctx.restore(); }
    // clip range shading (range players)
    if (this.range) { ctx.fillStyle = alphaOf(C.ink, 0.06); var cs = this.xOf(this.clipStart()), ce = this.xOf(this.clipEnd()); if (cs > x0) ctx.fillRect(x0, RULER, cs - x0, H - RULER); if (ce < x1) ctx.fillRect(ce, RULER, x1 - ce, H - RULER); }
    // notes
    var litGlow = !reduced.matches, minW = 1.5, i, n;
    var vis0 = tA - 8, vis1 = tB;   // notes can be up to a few seconds long
    for (i = 0; i < this.notes.length; i++) {
      n = this.notes[i];
      if (n.t > vis1) break;
      if (n.t + n.d < tA && n.t < vis0) continue;
      if (n.t + n.d < tA) continue;
      var col = C.ch[n.ch], lit = t != null && t >= n.t && t < n.t + n.d;
      var xa = this.xOf(n.t), wd = Math.max(minW, n.d * pxPerSec);
      var alpha = (0.45 + 0.55 * clamp(n.vol, 0, 15) / 15) * (n.echo ? 0.55 : 1);
      if (n.ch === 3) {
        var ny = g.noiseY(n.midi), th = 4 + 10 * clamp(n.vol, 0, 15) / 15;
        ctx.fillStyle = lit ? C.lit : alphaOf(col, alpha);
        if (lit && litGlow) { ctx.shadowColor = col; ctx.shadowBlur = 8; }
        ctx.fillRect(xa, ny - th / 2, Math.max(2, Math.min(wd, n.dec ? n.dec * pxPerSec : wd)), th);
        ctx.shadowBlur = 0;
        if (pxPerRow >= 14 && n.drum) { ctx.fillStyle = C.muted; ctx.font = '9px system-ui,sans-serif'; ctx.fillText(n.drum, xa + 3, ny + 3); }
        continue;
      }
      var y = g.pitchY(n.midi), hgt = Math.max(2, g.rowH - 1), solid = n.dec && n.dec < n.d ? n.dec * pxPerSec : wd;
      var fill = lit ? C.lit : alphaOf(col, alpha);
      if (lit && litGlow) { ctx.shadowColor = col; ctx.shadowBlur = 10; }
      if (n.arp && pxPerSec * n.arp_f / this.fps >= 1.5) {         // the chord cycle, step by step
        var ivs = n.arp.filter(function (x) { return x < 255; }), stepW = n.arp_f / this.fps * pxPerSec, k = 0;
        for (var xs = xa; xs < xa + wd - 0.5; xs += stepW, k++) { var iv = ivs[k % ivs.length] || 0; ctx.fillStyle = fill; ctx.fillRect(xs, g.pitchY(n.midi + iv), Math.min(stepW, xa + wd - xs), hgt); }
      } else {
        if (n.arp) { var ivs2 = n.arp.filter(function (x) { return x < 255; }), top = g.pitchY(n.midi + Math.max.apply(null, ivs2)); ctx.fillStyle = alphaOf(col, 0.22); ctx.fillRect(xa, top, wd, y - top + hgt); }
        ctx.fillStyle = fill; ctx.fillRect(xa, y, Math.min(solid, wd), hgt);
        if (solid < wd) { ctx.fillStyle = alphaOf(col, 0.2); ctx.fillRect(xa + solid, y, wd - solid, hgt); }
      }
      ctx.shadowBlur = 0;
      if (n.echo && wd > 6) { ctx.save(); ctx.setLineDash([2, 2]); ctx.strokeStyle = alphaOf(col, 0.9); ctx.strokeRect(xa + 0.5, y + 0.5, wd - 1, hgt - 1); ctx.restore(); }
      if (n.pan != null && wd >= 3) {   // a bright wedge on the side the note sits on (both edges for an auto-pan)
        var ww = Math.min(3, wd / 2);
        ctx.fillStyle = lit ? C.playhead : C.lit;
        if (n.pan === -1 || n.pan === 'LR') ctx.fillRect(xa, y, ww, hgt);
        if (n.pan === 1 || n.pan === 'LR') ctx.fillRect(xa + wd - ww, y, ww, hgt);
      }
      if (pxPerRow >= 4) {   // pitch motion
        ctx.strokeStyle = lit ? C.lit : alphaOf(col, 0.95); ctx.lineWidth = 1.5;
        var yc = y + hgt / 2;
        if (n.trill || n.mordent) { var ivT = n.trill || n.mordent, wT = n.trill ? wd : Math.min(wd, 2 / this.fps * pxPerSec + 1); ctx.fillStyle = alphaOf(col, 0.5); ctx.fillRect(xa, g.pitchY(n.midi + ivT), Math.max(2, wT), hgt); }
        if (n.bend) { ctx.beginPath(); ctx.moveTo(xa, g.pitchY(n.midi + n.bend[0]) + hgt / 2); ctx.lineTo(xa + n.bend[1] / this.fps * pxPerSec, yc); ctx.stroke(); }
        if (n.porta && n.porta_from != null) { ctx.beginPath(); ctx.moveTo(xa, g.pitchY(n.porta_from) + hgt / 2); ctx.lineTo(xa + n.porta / this.fps * pxPerSec, yc); ctx.stroke(); }
        if (n.penv) { ctx.beginPath(); ctx.moveTo(xa, g.pitchY(n.midi + n.penv[0]) + hgt / 2); ctx.lineTo(xa + n.penv[1] / this.fps * pxPerSec, yc); ctx.stroke(); }
        if (n.slide) { ctx.beginPath(); ctx.moveTo(xa, yc); ctx.lineTo(xa + wd, yc + (n.slide > 0 ? 1 : -1) * Math.min(wd * 0.5, g.rowH * 3)); ctx.stroke(); }
        if ((n.vib || n.autovib) && wd > 14 && g.rowH >= 5) { ctx.beginPath(); var vs = n.vib ? xa : xa + (n.autovib[1] / this.fps) * pxPerSec; for (var vx = vs; vx < xa + wd - 2; vx += 2) ctx.lineTo(vx, yc + ((vx - vs) / 2 % 2 ? 1.2 : -1.2)); ctx.stroke(); }
        ctx.lineWidth = 1;
      }
    }
    ctx.restore();
    // ruler
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, RULER);
    ctx.strokeStyle = C.gridStrong; ctx.beginPath(); ctx.moveTo(x0, RULER + 0.5); ctx.lineTo(x1, RULER + 0.5); ctx.stroke();
    ctx.fillStyle = C.muted; ctx.font = '10px system-ui,sans-serif'; ctx.textBaseline = 'middle';
    var labelStep = pxPerBar >= 28 ? 1 : pxPerBar >= 14 ? 2 : pxPerBar >= 7 ? 4 : pxPerBar >= 3.5 ? 8 : 16;
    for (b = b0; b < b1; b++) if (b % labelStep === 0) ctx.fillText(String(b + 1), this.xOf(b * this.secPerBar) + 3, RULER / 2);
    for (i = 0; i < this.sections.length; i++) { var s = this.sections[i], sx = this.xOf(s.start_bar * this.secPerBar); if (sx < x0 - 2 || sx > x1) continue;
      ctx.fillStyle = C.ink; ctx.font = 'bold 10px system-ui,sans-serif'; var lab = String(s.label); var maxW = Math.max(0, Math.min(x1, this.xOf((s.start_bar + s.bars) * this.secPerBar)) - sx - 22);
      while (lab.length > 1 && ctx.measureText(lab).width > maxW) lab = lab.slice(0, -1); if (maxW > 8) ctx.fillText(lab, Math.max(x0, sx) + 18, RULER / 2);
      ctx.strokeStyle = C.ink; ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.moveTo(Math.round(sx) + 0.5, 0); ctx.lineTo(Math.round(sx) + 0.5, RULER); ctx.stroke(); ctx.globalAlpha = 1; ctx.fillStyle = C.muted; ctx.font = '10px system-ui,sans-serif'; }
    // pitch gutter
    ctx.fillStyle = C.bg; ctx.fillRect(0, RULER, GUTTER, H - RULER);
    ctx.fillStyle = C.muted; ctx.textAlign = 'right';
    var every = g.rowH >= 7 ? 1 : 12;
    for (m = this.pLo; m <= this.pHi; m++) if (m % 12 === 0 || (every === 1 && !BLACK[m % 12] && g.rowH >= 9)) ctx.fillText(noteName(m), GUTTER - 4, g.pitchY(m) + g.rowH / 2);
    ctx.fillText('noise', GUTTER - 4, g.noiseTop + NOISE_H / 2);
    ctx.textAlign = 'left';
    // hover guide
    if (this.hover && this.hover.x >= x0 && !this.playing) { ctx.strokeStyle = alphaOf(C.ink, 0.35); ctx.beginPath(); var hx = Math.round(this.hover.x) + 0.5; ctx.moveTo(hx, RULER); ctx.lineTo(hx, H); ctx.stroke(); }
    // playhead
    if (t != null && t >= tA - 0.001 && t <= tB + 0.001) {
      var px = this.xOf(t);
      ctx.strokeStyle = C.playhead; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, H); ctx.stroke(); ctx.lineWidth = 1;
      ctx.fillStyle = C.playhead; ctx.beginPath(); ctx.moveTo(px - 5, 0); ctx.lineTo(px + 5, 0); ctx.lineTo(px, 7); ctx.closePath(); ctx.fill();
      this.playheadX = px;
    } else this.playheadX = null;
    this.updatePos();
  };
  Roll.prototype.drawPanStrip = function (ctx, g, x0, x1, tA, tB) {   // each pulse channel's side over time: L in the top half, R in the bottom half
    var top = g.panTop, half = (PAN_H - 4) / 2, C = this.colors, self = this;
    ctx.strokeStyle = C.grid; ctx.beginPath(); ctx.moveTo(x0, top + 0.5); ctx.lineTo(x1, top + 0.5); ctx.stroke();
    ctx.fillStyle = C.muted; ctx.font = '9px system-ui,sans-serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText('L', GUTTER - 4, top + 2 + half / 2); ctx.fillText('R', GUTTER - 4, top + 2 + half + half / 2); ctx.textAlign = 'left';
    for (var c = 0; c < 2; c++) {
      var segs = this.pans[c], side = 0, tPrev = 0;
      var paint = function (from, to, sd) {
        if (sd === 0 || to <= tA || from >= tB) return;
        var xa = Math.max(x0, self.xOf(from)), xb = Math.min(x1, self.xOf(to));
        ctx.fillStyle = alphaOf(C.ch[c], 0.85);
        ctx.fillRect(xa, top + 2 + (sd < 0 ? 0 : half) + c * 1.5, Math.max(1, xb - xa), Math.max(1, half - 3));
      };
      for (var i = 0; i < segs.length; i++) { paint(tPrev, segs[i][0], side); side = segs[i][1]; tPrev = segs[i][0]; }
      paint(tPrev, this.length, side);
    }
  };
  Roll.prototype.redraw = function () { this.draw(this.time()); };
  Roll.prototype.destroy = function () {
    this.destroyed = true; this.unbind();
    if (this.raf) global.cancelAnimationFrame(this.raf);
    if (this.ro) this.ro.disconnect(); if (this.mo) this.mo.disconnect();
    if (this.mql && this.mql.removeEventListener) this.mql.removeEventListener('change', this.onMedia);
    if (this.root.parentNode) this.root.parentNode.removeChild(this.root);
  };

  // ---- declarative mounting: <figure data-pianoroll data-events="#id of a <script type=application/json>" data-audio="#id"
  //      data-offset="0.71" data-range="34.3,36.4" data-title="..." data-height="240" data-sections="#id">
  function mountAll(root) {
    root = root || global.document;
    var out = [], figs = root.querySelectorAll('[data-pianoroll]');
    for (var i = 0; i < figs.length; i++) {
      var f = figs[i];
      if (f.__roll) { out.push(f.__roll); continue; }
      try {
        var src = f.getAttribute('data-events'), data = null;
        if (src) { var s = root.querySelector(src) || global.document.getElementById(src.replace(/^#/, '')); data = JSON.parse(s.textContent); }
        else { var inline = f.querySelector('script[type="application/json"]'); data = JSON.parse(inline.textContent); }
        var opts = { title: f.getAttribute('data-title') || undefined, height: f.getAttribute('data-height') ? +f.getAttribute('data-height') : undefined };
        if (f.getAttribute('data-offset')) opts.offset = +f.getAttribute('data-offset');
        if (f.getAttribute('data-range')) opts.range = f.getAttribute('data-range').split(',').map(Number);
        if (f.getAttribute('data-sections')) { var se = root.querySelector(f.getAttribute('data-sections')); if (se) opts.sections = JSON.parse(se.textContent); }
        if (f.getAttribute('data-audio')) opts.audio = root.querySelector(f.getAttribute('data-audio')) || global.document.getElementById(f.getAttribute('data-audio').replace(/^#/, ''));
        if (f.getAttribute('data-follow') === 'false') opts.follow = false;
        var roll = new Roll(f, data, opts);
        f.__roll = roll; out.push(roll);
      } catch (e) { if (global.console) console.warn('pianoroll: could not mount', f, e); }
    }
    return out;
  }

  global.GbcPianoRoll = { create: function (container, data, opts) { return new Roll(container, data, opts); }, mountAll: mountAll, FPS: FPS, Roll: Roll, version: '1.1.0' };
})(typeof window !== 'undefined' ? window : this);

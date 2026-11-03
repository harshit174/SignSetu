/* SignSetu browser speech: sounds like a person instead of a default system voice.
   Injected by app.py (say()) with __ITEMS__ = [{text, lang, fallback}] and __OPTS__ = {rate, interrupt}.
   - picks the most natural installed voice (neural / enhanced / Google) and avoids novelty and espeak voices
   - speaks one sentence at a time with a short breath between them, and lifts the pitch on questions
   - queues behind speech already in progress, unless interrupt is set (then it cuts in cleanly) */
(function (items, opts) {
  const W = window.parent, synth = W.speechSynthesis;
  if (!synth) return;
  const S = (W.__signsetu = W.__signsetu || { tok: 0, chain: Promise.resolve() });
  if (opts.interrupt) { S.tok++; synth.cancel(); S.chain = Promise.resolve(); }
  const tok = S.tok;

  const NOVELTY = /albert|bad news|bahh|bells|boing|bubbles|cellos|wobble|deranged|good news|hysterical|jester|organ|superstar|trinoids|whisper|zarvox|fred|junior|ralph|kathy/i;
  const WARM = /\b(isha|rishi|neerja|prabhat|swara|madhur|lekha|kajal|samantha|karen|daniel|serena|moira|tessa)\b/i;
  const norm = (l) => l.replace('_', '-').toLowerCase();

  function score(v, lang) {
    const vl = norm(v.lang), want = lang.toLowerCase(), pref = want.slice(0, 2);
    if (!vl.startsWith(pref)) return -Infinity;
    let s = vl === want ? 40 : (pref === 'en' && /^en-(gb|au)/.test(vl) ? 20 : 10);
    if (/natural|neural|online/i.test(v.name)) s += 60;        // Edge / Windows neural voices
    if (/premium|enhanced|siri/i.test(v.name)) s += 45;        // macOS / iOS downloaded voices
    if (/^google/i.test(v.name)) s += 30;                      // Chrome network voices
    if (WARM.test(v.name)) s += 25;
    if (!v.localService) s += 5;
    if (NOVELTY.test(v.name)) s -= 300;
    if (/espeak/i.test(v.name)) s -= 100;
    return s;
  }
  function pick(voices, lang) {
    let best = null, top = -Infinity;
    for (const v of voices) { const s = score(v, lang); if (s > top) { top = s; best = v; } }
    return best;
  }
  const voicesReady = () => new Promise((res) => {
    if (synth.getVoices().length) return res();
    synth.addEventListener('voiceschanged', () => res(), { once: true });
    setTimeout(res, 600);
  });
  const pause = (ms) => new Promise((r) => setTimeout(r, ms));

  function say(text, lang, voice) {
    return new Promise((res) => {
      if (tok !== S.tok) return res();
      const u = new W.SpeechSynthesisUtterance(text);
      if (voice) { u.voice = voice; u.lang = voice.lang; } else { u.lang = lang; }
      const q = /\?\s*$/.test(text), ex = /[!！]\s*$/.test(text);
      const jitter = 1 + (Math.random() - 0.5) * 0.04;        // tiny variation avoids a metronome delivery
      u.rate = Math.min(Math.max(opts.rate * jitter * (q ? 0.98 : ex ? 1.03 : 1), 0.5), 1.6);
      u.pitch = q ? 1.08 : ex ? 1.04 : 1.0;
      const done = () => res();
      u.onend = u.onerror = done;
      setTimeout(done, 2500 + text.length * 130);               // Chrome occasionally never fires onend
      synth.speak(u);
    });
  }

  S.chain = S.chain.then(async () => {
    await voicesReady();
    const voices = synth.getVoices();
    for (const it of items) {
      let lang = it.lang, text = it.text, voice = pick(voices, lang);
      if (!voice && lang.startsWith('hi')) { lang = 'en-IN'; text = it.fallback; voice = pick(voices, lang); }
      const sentences = (text.match(/[^.!?।]+[.!?।]*/g) || [text]).map((s) => s.trim()).filter(Boolean);
      for (const s of sentences) {
        if (tok !== S.tok) return;
        await say(s, lang, voice);
        await pause(/[?]\s*$/.test(s) ? 260 : 180);
      }
    }
  });
})(__ITEMS__, __OPTS__);

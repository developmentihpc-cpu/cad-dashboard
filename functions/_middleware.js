// Sign-in for the Cloudflare Pages copy of the dashboard (cad-dashboard.pages.dev).
// Every request passes through here; without a valid session cookie the visitor gets the sign-in page.
//
// Two modes:
// 1. Request-and-approve (when the KV binding CAD_KV and an email sender are set: MAIL_RELAY_URL + MAIL_RELAY_TOKEN
//    for the Google Apps Script relay in mail_relay.gs, or BREVO_API_KEY):
//    - anyone can request access (/__request); admins get an email and approve or decline on /__admin;
//    - approved people sign in with a 6-digit code sent to their email (no passwords);
//    - admins: ADMIN_EMAILS (comma-separated; default developmentihpc@gmail.com). With the relay, emails come
//      from the Gmail account that deployed the script; with Brevo, from MAIL_FROM (default the first admin).
//    - KV keys: user:<email> and req:<email> (details in metadata), code:<email> (10 min), rl:<email> (60 s).
// 2. Passwords (fallback while 1 is not set up): secret CAD_USERS (or users) = "email:password, email:password".
// In mode 1 the emails in CAD_USERS still count as approved (they sign in with a code).

const COOKIE = 'cad_session';
const SESSION_DAYS = 7;
const CODE_MINUTES = 10;
const PUBLIC_PATHS = new Set(['/logo.png', '/favicon.ico']);
const DEFAULT_ADMINS = 'developmentihpc@gmail.com';

const enc = new TextEncoder();
const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const sha = async s => b64url(await crypto.subtle.digest('SHA-256', enc.encode(s)));
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const cleanEmail = s => String(s || '').trim().toLowerCase();
const validEmail = e => /^[^\s@<>"',;:]+@[^\s@<>"',;:]+\.[a-z]{2,}$/i.test(e) && e.length <= 200;
const short = (s, n) => String(s || '').trim().slice(0, n);

function parseUsers(raw) {
  const users = new Map();
  const unquote = s => s.trim().replace(/^["'`<\s]+|["'`>\s]+$/g, '');
  for (let entry of String(raw || '').split(/[\r\n,;]+/)) {
    entry = unquote(entry);
    let i = entry.indexOf(':');
    if (i < 1) i = entry.search(/\s/);   // "email password" (space instead of a colon)
    if (i < 1) continue;
    const email = unquote(entry.slice(0, i)).toLowerCase(), pass = unquote(entry.slice(i + 1));
    if (email && pass) users.set(email, pass);
  }
  return users;
}

function sameText(a, b) {   // constant-time comparison
  const x = enc.encode(a), y = enc.encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) d |= (x[i] || 0) ^ (y[i] || 0);
  return d === 0;
}

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey('raw', await crypto.subtle.digest('SHA-256', enc.encode(secret + '|cad-dashboard-session')),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return b64url(await crypto.subtle.sign('HMAC', key, enc.encode(msg)));
}

// ── Configuration ─────────────────────────────────────────────────────────
function config(env) {
  const legacy = parseUsers(env.CAD_USERS || env.USERS || env.users || env.Users);
  const admins = String(env.ADMIN_EMAILS || DEFAULT_ADMINS).split(/[\s,;]+/).map(cleanEmail).filter(Boolean);
  const kv = env.CAD_KV, brevo = env.BREVO_API_KEY;
  const relay = env.MAIL_RELAY_URL, relayToken = env.MAIL_RELAY_TOKEN;
  const mail = !!((relay && relayToken) || brevo);
  return { legacy, admins, kv, brevo, relay: relay && relayToken ? relay : null, relayToken, approvals: !!(kv && mail),
           from: cleanEmail(env.MAIL_FROM) || admins[0], secret: env.SESSION_KEY || relayToken || brevo || '' };
}

async function isApproved(cfg, email) {
  if (!email) return false;
  if (cfg.admins.includes(email) || cfg.legacy.has(email)) return true;
  return !!(cfg.kv && await cfg.kv.get('user:' + email));
}

// ── Sessions ──────────────────────────────────────────────────────────────
// Code mode: signed with SESSION_KEY (or the Brevo key); password mode: signed with the person's own password.
// Every request re-checks that the person is still approved, so removing someone ends their access.
const sessionSecret = (cfg, email) => cfg.approvals ? cfg.secret : cfg.legacy.get(email);

async function makeCookie(cfg, email) {
  const exp = String(Date.now() + SESSION_DAYS * 864e5);
  const value = encodeURIComponent([b64url(enc.encode(email)), exp, await hmac(sessionSecret(cfg, email), email + '|' + exp)].join('|'));
  return `${COOKIE}=${value}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
}

async function sessionEmail(request, cfg) {
  const m = (request.headers.get('Cookie') || '').match(new RegExp('(?:^|;\\s*)' + COOKIE + '=([^;]+)'));
  if (!m) return null;
  const [e64, exp, sig] = decodeURIComponent(m[1]).split('|');
  if (!e64 || !exp || !sig || Date.now() > Number(exp)) return null;
  let email;
  try { email = atob(e64.replace(/-/g, '+').replace(/_/g, '/')); } catch (e) { return null; }
  const secret = sessionSecret(cfg, email);
  if (!secret || !sameText(sig, await hmac(secret, email + '|' + exp))) return null;
  return (await isApproved(cfg, email)) ? email : null;
}

// ── Email: Google Apps Script relay (mail_relay.gs, sends from the admin's Gmail) or Brevo ──
async function sendMail(cfg, to, subject, text) {
  const html = '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.55;color:#0F2A40">' +
    esc(text).replace(/(https:\/\/[^\s<]+)/g, '<a href="$1">$1</a>').replace(/\n/g, '<br>') + '</div>';
  if (cfg.relay) {
    const r = await fetch(cfg.relay, { method: 'POST', headers: { 'Content-Type': 'application/json' }, redirect: 'follow',
      body: JSON.stringify({ token: cfg.relayToken, to, subject, text, html }) });
    const out = await r.text();
    if (!r.ok || !/"ok"\s*:\s*true/.test(out)) throw new Error('Mail relay ' + r.status + ' ' + out.slice(0, 200));
    return;
  }
  const r = await fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: { 'api-key': cfg.brevo, 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ sender: { email: cfg.from, name: 'Country Assessment Dashboard' }, to: [{ email: to }],
                           subject, textContent: text, htmlContent: html }),
  });
  if (!r.ok) throw new Error('Brevo ' + r.status + ' ' + (await r.text()).slice(0, 200));
}

// ── Pages ─────────────────────────────────────────────────────────────────
function page(title, body, status = 200, extraHead = '') {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · Country Assessment Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:wght@600&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root { --ink:#0F2A40; --mute:#5D7186; --line:#E4ECF3; --gold:#B08D57; --bg:#F5F8FB; --err:#B3261E; --ok:#1E7B4F; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:flex-start; justify-content:center; background:var(--bg);
         font-family:Inter,system-ui,sans-serif; color:var(--ink); padding:48px 16px; }
  .card { width:100%; max-width:420px; background:#fff; border:1px solid var(--line); border-top:3px solid var(--gold);
          border-radius:10px; padding:32px 28px; box-shadow:0 8px 30px rgba(15,42,64,.06); }
  .wide { max-width:860px; }
  img.logo { height:44px; display:block; margin-bottom:22px; }
  h1 { font-family:Lora,Georgia,serif; font-size:22px; margin:0 0 6px; }
  h2 { font-family:Lora,Georgia,serif; font-size:17px; margin:28px 0 10px; }
  .sub { color:var(--mute); font-size:14px; margin:0 0 20px; line-height:1.55; }
  .ar { font-family:'IBM Plex Sans Arabic',sans-serif; direction:rtl; display:block; }
  label { display:block; font-size:12px; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color:var(--mute); margin:14px 0 6px; }
  input, textarea { width:100%; padding:11px 12px; font-size:15px; border:1px solid #CBD6E1; border-radius:6px; font-family:inherit; color:var(--ink); }
  textarea { min-height:80px; resize:vertical; }
  input:focus, textarea:focus { outline:2px solid #0A6FD1; outline-offset:1px; border-color:#0A6FD1; }
  .code { font-size:24px; letter-spacing:.4em; text-align:center; }
  button { width:100%; margin-top:20px; padding:12px; font-size:15px; font-weight:600; color:#fff; background:var(--ink);
           border:0; border-radius:6px; cursor:pointer; font-family:inherit; }
  button:hover { background:#1B3E5C; }
  .msg { margin:0 0 8px; padding:10px 12px; font-size:13.5px; border-radius:6px; line-height:1.5; }
  .err { color:var(--err); background:#FCEEEE; } .ok { color:var(--ok); background:#E9F6EF; }
  .foot { margin-top:20px; font-size:13px; color:var(--mute); line-height:1.6; }
  a { color:#0A6FD1; }
  table { width:100%; border-collapse:collapse; font-size:13.5px; }
  th { text-align:left; font-size:11.5px; text-transform:uppercase; letter-spacing:.04em; color:var(--mute); padding:8px 6px; border-bottom:1px solid var(--line); }
  td { padding:9px 6px; border-bottom:1px solid var(--line); vertical-align:top; overflow-wrap:anywhere; }
  td form { display:inline; } td button { width:auto; margin:0 4px 4px 0; padding:6px 12px; font-size:13px; }
  .alt { background:#fff; color:var(--ink); border:1px solid #CBD6E1; } .alt:hover { background:#F0F4F8; }
  .tblwrap { overflow-x:auto; } .empty { color:var(--mute); font-size:14px; }
</style>${extraHead}</head><body><main class="card${title === 'Admin' ? ' wide' : ''}">
<img class="logo" src="/logo.png" alt="Office of Development Affairs">${body}</main></body></html>`;
  return new Response(html, { status, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Frame-Options': 'DENY', 'X-Robots-Tag': 'noindex' } });
}
const msg = (text, kind = 'err') => text ? `<p class="msg ${kind}" role="${kind === 'err' ? 'alert' : 'status'}">${text}</p>` : '';
const SPAM_NOTE = 'The email can take a minute to arrive. Please check your spam or junk folder too.';

function emailPage(cfg, next, note = '', status = 200) {
  if (!cfg.approvals) return passwordPage(next, note, status);
  return page('Sign in', `<h1>Country Assessment Dashboard</h1>
  <p class="sub">Enter your email and we will send you a sign-in code.<span class="ar">أدخل بريدك الإلكتروني وسنرسل إليك رمز الدخول.</span></p>
  ${note}
  <form method="post" action="/__code"><input type="hidden" name="next" value="${esc(next)}">
    <label for="email">Email · البريد الإلكتروني</label>
    <input id="email" name="email" type="email" autocomplete="email" required autofocus>
    <button type="submit">Send code · إرسال الرمز</button></form>
  <p class="foot">No access yet? <a href="/__request">Request access</a> · <a href="/__request">طلب الوصول</a></p>`, status);
}

function codePage(email, next, note = '', status = 200) {
  return page('Enter code', `<h1>Check your email</h1>
  <p class="sub">If <strong>${esc(email)}</strong> has access, a 6-digit code is on its way. It is valid for ${CODE_MINUTES} minutes.
  <span class="ar">إذا كان لهذا البريد صلاحية الوصول، فقد أُرسل إليه رمز من 6 أرقام صالح لمدة ${CODE_MINUTES} دقائق.</span></p>
  ${note}
  <form method="post" action="/__verify"><input type="hidden" name="next" value="${esc(next)}"><input type="hidden" name="email" value="${esc(email)}">
    <label for="code">Code · الرمز</label>
    <input id="code" name="code" class="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9 ]{6,8}" maxlength="8" required autofocus>
    <button type="submit">Sign in · تسجيل الدخول</button></form>
  <p class="foot">${SPAM_NOTE}<br><a href="/">Use a different email or send a new code</a></p>`, status);
}

function passwordPage(next, note = '', status = 200) {
  return page('Sign in', `<h1>Country Assessment Dashboard</h1>
  <p class="sub">Sign in with the email and password you were given.<span class="ar">سجّل الدخول بالبريد الإلكتروني وكلمة المرور المرسلة إليك.</span></p>
  ${note}
  <form method="post" action="/__login"><input type="hidden" name="next" value="${esc(next)}">
    <label for="email">Email · البريد الإلكتروني</label>
    <input id="email" name="email" type="email" autocomplete="username" required autofocus>
    <label for="password">Password · كلمة المرور</label>
    <input id="password" name="password" type="password" autocomplete="current-password" required>
    <button type="submit">Sign in · تسجيل الدخول</button></form>
  <p class="foot">Access is limited to approved users. If you need access or have forgotten your password, contact the Office of Development Affairs team.</p>`, status);
}

function requestPage(note = '', v = {}, status = 200) {
  return page('Request access', `<h1>Request access</h1>
  <p class="sub">Tell us who you are. You will receive an email once your request has been reviewed.
  <span class="ar">عرّف بنفسك، وستصلك رسالة بالبريد الإلكتروني بعد مراجعة طلبك.</span></p>
  ${note}
  <form method="post" action="/__request">
    <label for="name">Full name · الاسم الكامل</label><input id="name" name="name" required maxlength="100" value="${esc(v.name)}">
    <label for="email">Work email · البريد الإلكتروني للعمل</label><input id="email" name="email" type="email" required maxlength="200" value="${esc(v.email)}">
    <label for="org">Organisation and role · الجهة والمنصب</label><input id="org" name="org" required maxlength="150" value="${esc(v.org)}">
    <label for="reason">Why you need access (optional) · سبب الطلب (اختياري)</label><textarea id="reason" name="reason" maxlength="400">${esc(v.reason)}</textarea>
    <button type="submit">Send request · إرسال الطلب</button></form>
  <p class="foot">Already approved? <a href="/">Sign in</a></p>`, status);
}

// ── Admin page ────────────────────────────────────────────────────────────
async function listAll(kv, prefix) {
  const out = []; let cursor;
  do { const r = await kv.list({ prefix, cursor }); out.push(...r.keys); cursor = r.list_complete ? null : r.cursor; } while (cursor);
  return out.map(k => ({ email: k.name.slice(prefix.length), ...(k.metadata || {}) }));
}
const day = t => t ? new Date(t).toISOString().slice(0, 10) : '';

async function adminPage(cfg, me, note = '') {
  const reqs = (await listAll(cfg.kv, 'req:')).sort((a, b) => (a.at || 0) - (b.at || 0));
  const users = (await listAll(cfg.kv, 'user:')).sort((a, b) => a.email.localeCompare(b.email));
  const btn = (action, email, label, cls = '') =>
    `<form method="post" action="/__admin/${action}"><input type="hidden" name="email" value="${esc(email)}"><button class="${cls}" type="submit">${label}</button></form>`;
  const reqRows = reqs.map(r => `<tr><td><strong>${esc(r.name)}</strong><br>${esc(r.email)}</td><td>${esc(r.org)}</td><td>${esc(r.reason)}</td>
    <td>${day(r.at)}</td><td>${btn('approve', r.email, 'Approve')}${btn('decline', r.email, 'Decline', 'alt')}</td></tr>`).join('');
  const userRows = users.map(u => `<tr><td><strong>${esc(u.name || '')}</strong><br>${esc(u.email)}</td><td>${esc(u.org || '')}</td>
    <td>${day(u.approvedAt)}${u.by ? '<br><span class="empty">by ' + esc(u.by) + '</span>' : ''}</td><td>${btn('remove', u.email, 'Remove', 'alt')}</td></tr>`).join('');
  const fixed = [...new Set([...cfg.admins, ...cfg.legacy.keys()])].map(e =>
    `<tr><td>${esc(e)}</td><td>${cfg.admins.includes(e) ? 'Admin' : 'From the CAD_USERS setting in Cloudflare'}</td></tr>`).join('');
  return page('Admin', `<h1>Dashboard access</h1>
  <p class="sub">Signed in as ${esc(me)} · <a href="/">Open the dashboard</a> · <a href="/__logout">Sign out</a></p>
  ${note}
  <form method="post" action="/__admin/add" style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;margin-top:8px">
    <div style="flex:2 1 220px"><label for="add-email">Give someone access directly</label><input id="add-email" name="email" type="email" placeholder="name@organisation.gov" required></div>
    <div style="flex:1 1 160px"><label for="add-name">Name (optional)</label><input id="add-name" name="name" maxlength="100"></div>
    <button type="submit" style="width:auto;margin:0;flex:0 0 auto">Add and email them</button></form>
  <h2>Pending requests (${reqs.length})</h2>
  ${reqs.length ? `<div class="tblwrap"><table><tr><th>Person</th><th>Organisation</th><th>Reason</th><th>Requested</th><th></th></tr>${reqRows}</table></div>` : '<p class="empty">No pending requests.</p>'}
  <h2>People with access (${users.length})</h2>
  ${users.length ? `<div class="tblwrap"><table><tr><th>Person</th><th>Organisation</th><th>Approved</th><th></th></tr>${userRows}</table></div>` : '<p class="empty">Nobody approved yet.</p>'}
  ${fixed ? `<h2>Always allowed</h2><div class="tblwrap"><table><tr><th>Email</th><th>Why</th></tr>${fixed}</table></div>
  <p class="foot">Admins are set by ADMIN_EMAILS in Cloudflare (default ${esc(DEFAULT_ADMINS)}). Delete the CAD_USERS setting once those people are added above.</p>` : ''}
  <p class="foot">Removing someone ends their access within about a minute.</p>`);
}

// ── Router ────────────────────────────────────────────────────────────────
const safeNext = n => (typeof n === 'string' && n.startsWith('/') && !n.startsWith('//') && (!n.startsWith('/__') || n === '/__admin')) ? n : '/';
const redirect = (to, cookie) => new Response(null, { status: 303, headers: { Location: to, ...(cookie ? { 'Set-Cookie': cookie } : {}) } });
const pause = ms => new Promise(r => setTimeout(r, ms));

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;
  const cfg = config(env);
  const post = request.method === 'POST';

  if (post) {   // forms must come from this site
    const origin = request.headers.get('Origin');
    if (origin && origin !== url.origin) return new Response('Forbidden', { status: 403 });
  }
  const form = post && path.startsWith('/__') ? await request.formData() : null;
  const f = k => form ? String(form.get(k) || '') : '';

  if (path === '/__logout') return redirect('/', `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`);

  // Password mode (fallback)
  if (path === '/__login' && post) {
    const email = cleanEmail(f('email')), pass = f('password'), target = safeNext(f('next'));
    const known = cfg.legacy.get(email);
    if (cfg.approvals || !known || !sameText(pass, known)) {
      await pause(800);
      return passwordPage(target, msg(cfg.legacy.size ? 'That email and password do not match an approved user.' : 'Access has not been set up yet.'), 401);
    }
    return redirect(target, await makeCookie(cfg, email));
  }

  // Code mode
  if (cfg.approvals) {
    if (path === '/__code' && post) {
      const email = cleanEmail(f('email')), target = safeNext(f('next'));
      if (!validEmail(email)) return emailPage(cfg, target, msg('Please enter a valid email address.'), 400);
      if (await cfg.kv.get('rl:' + email)) return codePage(email, target, msg('A code was sent less than a minute ago. Please use that one or wait a minute.'));
      if (await isApproved(cfg, email)) {
        const code = String(crypto.getRandomValues(new Uint32Array(1))[0] % 1e6).padStart(6, '0');
        await cfg.kv.put('code:' + email, JSON.stringify({ h: await sha(email + '|' + code), tries: 0 }), { expirationTtl: CODE_MINUTES * 60 });
        await cfg.kv.put('rl:' + email, '1', { expirationTtl: 60 });
        try {
          await sendMail(cfg, email, `Your sign-in code: ${code}`,
            `Your code for the Country Assessment Dashboard is ${code}\n\nIt is valid for ${CODE_MINUTES} minutes. If you did not ask for it, you can ignore this email.\n\nرمز الدخول إلى لوحة تقييم الدول: ${code}`);
        } catch (e) {
          return emailPage(cfg, target, msg('The code could not be sent just now. Please try again in a few minutes.'), 502);
        }
      } else await pause(400);   // same answer either way, so the page does not reveal who has access
      return codePage(email, target);
    }
    if (path === '/__verify' && post) {
      const email = cleanEmail(f('email')), code = f('code').replace(/\D/g, ''), target = safeNext(f('next'));
      const raw = await cfg.kv.get('code:' + email);
      const rec = raw ? JSON.parse(raw) : null;
      if (!rec || rec.tries >= 5) return emailPage(cfg, target, msg('That code has expired. Please request a new one.'), 401);
      if (!sameText(await sha(email + '|' + code), rec.h) || !(await isApproved(cfg, email))) {
        rec.tries++;
        await cfg.kv.put('code:' + email, JSON.stringify(rec), { expirationTtl: CODE_MINUTES * 60 });
        await pause(600);
        return codePage(email, target, msg('That code is not right. Please check it and try again.'), 401);
      }
      await cfg.kv.delete('code:' + email);
      return redirect(target, await makeCookie(cfg, email));
    }
    if (path === '/__request') {
      if (!post) return requestPage();
      const v = { name: short(f('name'), 100), email: cleanEmail(f('email')), org: short(f('org'), 150), reason: short(f('reason'), 400) };
      if (!v.name || !v.org || !validEmail(v.email)) return requestPage(msg('Please fill in your name, a valid email and your organisation.'), v, 400);
      if (await isApproved(cfg, v.email)) return emailPage(cfg, '/', msg('This email already has access. Enter it below to get a sign-in code.', 'ok'));
      const existing = await cfg.kv.get('req:' + v.email);
      await cfg.kv.put('req:' + v.email, '1', { metadata: { name: v.name, org: v.org, reason: short(v.reason, 300), at: Date.now() } });
      if (!existing) {
        const text = `New access request for the Country Assessment Dashboard\n\nName: ${v.name}\nEmail: ${v.email}\nOrganisation: ${v.org}\nReason: ${v.reason || '—'}\n\nApprove or decline: ${url.origin}/__admin`;
        await Promise.allSettled(cfg.admins.map(a => sendMail(cfg, a, `Access request: ${v.name} (${v.org})`, text)));
      }
      return page('Request sent', `<h1>Request sent</h1><p class="sub">Thank you, ${esc(v.name)}. We will email <strong>${esc(v.email)}</strong> once your request has been reviewed.
        <span class="ar">شكراً لك. سنراسلك عبر البريد الإلكتروني بعد مراجعة طلبك.</span></p><p class="foot">${SPAM_NOTE}</p>`);
    }
  }

  if (PUBLIC_PATHS.has(path)) return next();
  const me = await sessionEmail(request, cfg);

  // Admin
  if (path === '/__admin' || path.startsWith('/__admin/')) {
    if (!cfg.approvals) return page('Admin', `<h1>Admin not set up</h1><p class="sub">The request-and-approve setup (CAD_KV plus the email relay) is not complete yet.</p>`, 503);
    if (!me) return emailPage(cfg, '/__admin');
    if (!cfg.admins.includes(me)) return page('Admin', `<h1>Not an admin</h1><p class="sub">${esc(me)} can use the dashboard but cannot manage access. <a href="/">Open the dashboard</a></p>`, 403);
    if (!post) return adminPage(cfg, me);
    const email = cleanEmail(f('email')), action = path.slice('/__admin/'.length);
    if (!validEmail(email)) return adminPage(cfg, me, msg('That email address is not valid.'));
    const signIn = `${url.origin}/`;
    const welcome = `Your access to the Country Assessment Dashboard has been approved.\n\nOpen ${signIn} and enter this email address (${email}). We will send you a 6-digit code to sign in.\n\nتمت الموافقة على وصولك إلى لوحة تقييم الدول. افتح الرابط أعلاه وأدخل بريدك الإلكتروني لتصلك رسالة برمز الدخول.`;
    if (action === 'approve' || action === 'add') {
      const meta = action === 'approve' ? ((await cfg.kv.getWithMetadata('req:' + email)).metadata || {}) : { name: short(f('name'), 100) };
      await cfg.kv.put('user:' + email, '1', { metadata: { name: meta.name || '', org: meta.org || '', approvedAt: Date.now(), by: me } });
      await cfg.kv.delete('req:' + email);
      let sent = true;
      try { await sendMail(cfg, email, 'Your access to the Country Assessment Dashboard', welcome); } catch (e) { sent = false; }
      return adminPage(cfg, me, msg(`${esc(email)} now has access.` + (sent ? ' They have been emailed.' : ' The email could not be sent; please let them know.'), sent ? 'ok' : 'err'));
    }
    if (action === 'decline') { await cfg.kv.delete('req:' + email); return adminPage(cfg, me, msg(`Request from ${esc(email)} declined. No email was sent.`, 'ok')); }
    if (action === 'remove') { await cfg.kv.delete('user:' + email); return adminPage(cfg, me, msg(`${esc(email)} no longer has access.`, 'ok')); }
    return adminPage(cfg, me);
  }

  if (me) {
    const res = await next();
    let out = new Response(res.body, res);
    out.headers.set('X-Robots-Tag', 'noindex');
    out.headers.set('Cache-Control', 'private, no-cache');
    const isHtml = (out.headers.get('Content-Type') || '').includes('text/html');
    if (isHtml && cfg.approvals && cfg.admins.includes(me)) {   // a small "Manage access" link for admins
      out = new HTMLRewriter().on('body', { element(el) { el.append(
        '<a href="/__admin" style="position:fixed;left:12px;bottom:12px;z-index:9999;background:#0F2A40;color:#fff;font:600 12px Inter,system-ui,sans-serif;padding:7px 12px;border-radius:999px;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.2)">Manage access</a>',
        { html: true }); } }).transform(out);
    }
    return out;
  }
  if (request.method !== 'GET' || /\.(json|js|png|css)$/.test(path) || path.startsWith('/__')) {
    if (path.startsWith('/__') && request.method === 'GET') return redirect('/');
    return new Response('Sign-in required', { status: 401 });
  }
  return emailPage(cfg, path + url.search);
}

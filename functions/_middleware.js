// Sign-in for the Cloudflare Pages copy of the dashboard (cad-dashboard.pages.dev).
// Every request passes through here; without a valid session cookie the visitor gets the sign-in page.
//
// Approved people live in ONE Cloudflare project secret, CAD_USERS (Settings → Variables and Secrets):
//   name@org.gov:password, other@partner.gov:another-password
// separated by commas, semicolons or new lines. Passwords may not contain commas or semicolons.
// Removing a person (or changing their password) ends their session at once. No secret set = nobody gets in.

const COOKIE = 'cad_session';
const SESSION_DAYS = 7;
const PUBLIC_PATHS = new Set(['/logo.png', '/favicon.ico']);

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

const enc = new TextEncoder();
const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

// A session is signed with a key made from that person's own password, so it stays valid only while
// their entry in CAD_USERS is unchanged.
async function sign(email, exp, pass) {
  const key = await crypto.subtle.importKey('raw', await crypto.subtle.digest('SHA-256', enc.encode(pass + '|cad-dashboard-session')),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return b64url(await crypto.subtle.sign('HMAC', key, enc.encode(email + '|' + exp)));
}

function sameText(a, b) {   // constant-time comparison
  const x = enc.encode(a), y = enc.encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) d |= (x[i] || 0) ^ (y[i] || 0);
  return d === 0;
}

async function sessionEmail(request, users) {
  const m = (request.headers.get('Cookie') || '').match(new RegExp('(?:^|;\\s*)' + COOKIE + '=([^;]+)'));
  if (!m) return null;
  const [e64, exp, sig] = decodeURIComponent(m[1]).split('|');
  if (!e64 || !exp || !sig || Date.now() > Number(exp)) return null;
  let email;
  try { email = atob(e64.replace(/-/g, '+').replace(/_/g, '/')); } catch (e) { return null; }
  const pass = users.get(email);
  if (!pass) return null;
  return sameText(sig, await sign(email, exp, pass)) ? email : null;
}

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function loginPage(next, error, status = 200) {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in · Country Assessment Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:wght@600&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root { --ink:#0F2A40; --mute:#5D7186; --line:#E4ECF3; --gold:#B08D57; --bg:#F5F8FB; --err:#B3261E; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; background:var(--bg);
         font-family:Inter,system-ui,sans-serif; color:var(--ink); padding:24px 16px; }
  .card { width:100%; max-width:400px; background:#fff; border:1px solid var(--line); border-top:3px solid var(--gold);
          border-radius:10px; padding:32px 28px; box-shadow:0 8px 30px rgba(15,42,64,.06); }
  img { height:44px; display:block; margin-bottom:22px; }
  h1 { font-family:Lora,Georgia,serif; font-size:22px; margin:0 0 6px; }
  .sub { color:var(--mute); font-size:14px; margin:0 0 22px; line-height:1.5; }
  .ar { font-family:'IBM Plex Sans Arabic',sans-serif; direction:rtl; }
  label { display:block; font-size:12px; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color:var(--mute); margin:14px 0 6px; }
  input { width:100%; padding:11px 12px; font-size:15px; border:1px solid #CBD6E1; border-radius:6px; font-family:inherit; color:var(--ink); }
  input:focus { outline:2px solid #0A6FD1; outline-offset:1px; border-color:#0A6FD1; }
  button { width:100%; margin-top:22px; padding:12px; font-size:15px; font-weight:600; color:#fff; background:var(--ink);
           border:0; border-radius:6px; cursor:pointer; font-family:inherit; }
  button:hover { background:#1B3E5C; }
  .err { margin:0 0 6px; padding:10px 12px; font-size:13.5px; color:var(--err); background:#FCEEEE; border-radius:6px; }
  .foot { margin-top:20px; font-size:12.5px; color:var(--mute); line-height:1.5; }
</style></head><body>
<main class="card">
  <img src="/logo.png" alt="Office of Development Affairs">
  <h1>Country Assessment Dashboard</h1>
  <p class="sub">Sign in with the email and password you were given.<br><span class="ar">سجّل الدخول بالبريد الإلكتروني وكلمة المرور المرسلة إليك.</span></p>
  ${error ? `<p class="err" role="alert">${esc(error)}</p>` : ''}
  <form method="post" action="/__login">
    <input type="hidden" name="next" value="${esc(next)}">
    <label for="email">Email · البريد الإلكتروني</label>
    <input id="email" name="email" type="email" autocomplete="username" required autofocus>
    <label for="password">Password · كلمة المرور</label>
    <input id="password" name="password" type="password" autocomplete="current-password" required>
    <button type="submit">Sign in · تسجيل الدخول</button>
  </form>
  <p class="foot">Access is limited to approved users. If you need access or have forgotten your password, contact the Office of Development Affairs team.</p>
</main></body></html>`;
  return new Response(html, { status, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Frame-Options': 'DENY', 'X-Robots-Tag': 'noindex' } });
}

const safeNext = n => (typeof n === 'string' && n.startsWith('/') && !n.startsWith('//')) ? n : '/';

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const users = parseUsers(env.CAD_USERS);

  if (url.pathname === '/__logout') {
    return new Response(null, { status: 302, headers: { Location: '/', 'Set-Cookie': `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` } });
  }

  if (url.pathname === '/__login' && request.method === 'POST') {
    const form = await request.formData();
    const email = String(form.get('email') || '').trim().toLowerCase(), pass = String(form.get('password') || '');
    const target = safeNext(String(form.get('next') || '/'));
    const known = users.get(email);
    if (!known || !sameText(pass, known)) {
      await new Promise(r => setTimeout(r, 800));   // slow down password guessing
      return loginPage(target, users.size ? 'That email and password do not match an approved user.' : 'Access has not been set up yet.', 401);
    }
    const exp = String(Date.now() + SESSION_DAYS * 864e5);
    const value = encodeURIComponent([b64url(enc.encode(email)), exp, await sign(email, exp, known)].join('|'));
    return new Response(null, { status: 303, headers: { Location: target,
      'Set-Cookie': `${COOKIE}=${value}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax` } });
  }

  if (PUBLIC_PATHS.has(url.pathname)) return next();
  if (await sessionEmail(request, users)) {
    const res = await next();
    const out = new Response(res.body, res);
    out.headers.set('X-Robots-Tag', 'noindex');
    out.headers.set('Cache-Control', 'private, no-cache');
    return out;
  }
  if (request.method !== 'GET' || url.pathname.match(/\.(json|js|png|css)$/)) return new Response('Sign-in required', { status: 401 });
  return loginPage(url.pathname + url.search);
}

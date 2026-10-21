// Email relay for the Country Needs Dashboard sign-in (functions/_middleware.js).
// Sends sign-in codes, access requests and approvals from the Gmail account that deploys this script.
//
// Setup (script.google.com, signed in as developmentihpc@gmail.com):
//   1. New project → paste this file over the sample code → Save.
//   2. Project Settings (gear) → Script Properties → Add property:
//        Property: TOKEN    Value: a long random phrase you make up (the same value goes into
//        Cloudflare as the secret MAIL_RELAY_TOKEN). Never put the token in this file.
//   3. Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy,
//      and allow the permissions Google asks for (sending email as you).
//   4. Copy the Web app URL into Cloudflare as the secret MAIL_RELAY_URL.
// After editing this script, use Deploy → Manage deployments → Edit → New version (the URL stays the same).

function doPost(e) {
  var out = function (obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); };
  try {
    var token = PropertiesService.getScriptProperties().getProperty('TOKEN');
    var req = JSON.parse(e.postData.contents);
    if (!token || req.token !== token) return out({ ok: false, error: 'unauthorised' });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(req.to || ''))) return out({ ok: false, error: 'bad recipient' });
    MailApp.sendEmail({
      to: req.to,
      subject: String(req.subject || '').slice(0, 200),
      body: String(req.text || ''),
      htmlBody: String(req.html || ''),
      name: 'Country Needs Dashboard'
    });
    return out({ ok: true, remaining: MailApp.getRemainingDailyQuota() });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

// Run once from the editor (select testRelay → Run) to approve the email permission and send yourself a test.
function testRelay() {
  MailApp.sendEmail(Session.getActiveUser().getEmail(), 'Dashboard mail relay works', 'This is a test from the Country Needs Dashboard mail relay.');
}

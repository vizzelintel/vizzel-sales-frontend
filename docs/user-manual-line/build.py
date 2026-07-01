#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — สร้างคู่มือการเข้าใช้งานระบบ Vizzel Sales ผ่าน LINE

ทำงาน 2 ขั้น:
  1) capture  : เปิด index.html / upload.html ด้วย Chromium (viewport มือถือ) พร้อม stub LIFF
                + mock fetch แล้วถ่ายภาพหน้าจอจริงของแต่ละขั้นตอน -> images/*.png
                ขั้นตอนฝั่ง LINE ที่ capture จาก code ไม่ได้ (เพิ่มเพื่อน OA / consent)
                จะสร้างเป็นภาพ placeholder (กรอบ + ข้อความ "แทรกภาพหน้าจอ") ให้เติมภายหลัง
  2) render   : เปิด manual.html แล้วสั่งพิมพ์เป็น PDF (A4) -> Vizzel-Sales-LINE-User-Manual.pdf

การใช้งาน:
  python3 build.py              # ทำทั้ง capture + render
  python3 build.py capture      # เฉพาะถ่ายภาพหน้าจอ
  python3 build.py render       # เฉพาะ render PDF

หมายเหตุ: ใช้ Chromium ที่ติดตั้งมากับ environment (PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers)
ไม่ต้องรัน `playwright install`
"""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))          # vizzel-sales-frontend
INDEX = os.path.join(REPO, "index.html")
UPLOAD = os.path.join(REPO, "upload.html")
IMG = os.path.join(HERE, "images")
MANUAL = os.path.join(HERE, "manual.html")
PDF_OUT = os.path.join(HERE, "Vizzel-Sales-LINE-User-Manual.pdf")

# viewport มือถือ (แนว LINE) — 390x844 @2x = ภาพคมชัด 780px กว้าง
MOBILE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)


def logo_data_uri():
    """ฝังโลโก้เป็น data URI (set_content โหลด file:// ไม่ได้เพราะ origin เป็น about:blank)"""
    import base64
    with open(os.path.join(REPO, "assets", "logo.png"), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def chromium_path():
    c = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
    if not c:
        raise RuntimeError("ไม่พบ Chromium ใน /opt/pw-browsers")
    return sorted(c)[-1]


# ── JS ที่ inject ก่อนสคริปต์ของหน้าเว็บ: stub LIFF + mock fetch ─────────────
# window.__SCN = ชื่อ scenario เพื่อให้ mock ตอบต่างกัน (เช่น ผู้ใช้ใหม่ vs ผู้ใช้เดิม)
INIT_JS = r"""
(() => {
  const USER = {
    id: "u-100", line_id: "Uxxxxxxxxxxxxxxx",
    full_name: "สมชาย ใจดี", first_name: "สมชาย", last_name: "ใจดี",
    role: "support", email: "somchai@example.com", phone: "0812345678",
    region: "ภาคกลาง", company_id: "c-1", company_name: "บริษัท วิซเซล อินเทล จำกัด",
    email_verified: true, created_at: "2026-01-15T09:00:00Z",
    picture: ""
  };
  const PROJECTS = [
    {id:"p-1", agency_name:"เทศบาลเมืองบุรีรัมย์", agency_type:"เทศบาลเมือง", region:"บุรีรัมย์",
     contact_person:"นางสาวมาลี สุขใจ", contact_position:"ผู้อำนวยการกองคลัง", contact_phone:"0812345678",
     status:"quotation", created_at:"2026-05-02T04:00:00Z", auto_reject_at:"2026-08-20T00:00:00Z"},
    {id:"p-2", agency_name:"องค์การบริหารส่วนจังหวัดขอนแก่น", agency_type:"องค์การบริหารส่วนจังหวัด", region:"ขอนแก่น",
     contact_person:"นายวิชัย ตั้งใจ", contact_position:"หัวหน้าฝ่ายพัสดุ", contact_phone:"0899999999",
     status:"tor", created_at:"2026-04-18T04:00:00Z", auto_reject_at:"2026-07-30T00:00:00Z"},
    {id:"p-3", agency_name:"โรงพยาบาลศูนย์เชียงราย", agency_type:"โรงพยาบาลศูนย์", region:"เชียงราย",
     contact_person:"นางพรทิพย์ ใจงาม", contact_position:"เจ้าหน้าที่จัดซื้อ", contact_phone:"0870000000",
     status:"register", created_at:"2026-06-01T04:00:00Z", auto_reject_at:"2026-09-10T00:00:00Z"},
    {id:"p-4", agency_name:"มหาวิทยาลัยราชภัฏนครราชสีมา", agency_type:"มหาวิทยาลัย", region:"นครราชสีมา",
     contact_person:"ผศ.ดร.สมหญิง เก่งกล้า", contact_position:"รองอธิการบดี", contact_phone:"0861111111",
     status:"contract", created_at:"2026-03-10T04:00:00Z"},
    {id:"p-5", agency_name:"เทศบาลตำบลหนองแวง", agency_type:"เทศบาลตำบล", region:"มหาสารคาม",
     contact_person:"นายอนุชา รักงาน", contact_position:"ปลัดเทศบาล", contact_phone:"0855555555",
     status:"closed", created_at:"2026-02-20T04:00:00Z"},
  ];
  const STATUS_COUNTS = {register:3, quotation:2, tor:1, contract:1, closed:4, reject:1};
  const PROJECT_DETAIL = PROJECTS[0];

  function json(obj, status) {
    return new Response(JSON.stringify(obj), {
      status: status || 200, headers: {"Content-Type": "application/json"}
    });
  }

  const origFetch = window.fetch;
  window.fetch = function (url, opts) {
    try {
      const u = (typeof url === "string") ? url : (url && url.url) || "";
      const method = (opts && opts.method || "GET").toUpperCase();
      if (u.indexOf("/api/v1/") === -1) {
        // ไม่ใช่ API — คืน 200 ว่าง (บล็อกเน็ตภายนอกไว้แล้ว)
        return Promise.resolve(json({}, 200));
      }
      // ── auth/line ──
      if (u.indexOf("/auth/line") !== -1) {
        if (window.__SCN === "register") {
          return Promise.resolve(json({
            error: "user_not_found",
            line_id: "Uxxxxxxxxxxxxxxx",
            display_name: "สมชาย ใจดี",
            picture_url: ""
          }, 401));
        }
        return Promise.resolve(json({token: "mock-jwt", user: USER}, 200));
      }
      if (u.indexOf("/auth/validate-invite") !== -1)
        return Promise.resolve(json({valid: true, company_id: "c-1", company_name: "บริษัท วิซเซล อินเทล จำกัด"}, 200));
      if (u.indexOf("/auth/register") !== -1)
        return Promise.resolve(json({token: "mock-jwt", user: USER}, 200));
      if (u.indexOf("/auth/email/send-otp") !== -1)
        return Promise.resolve(json({ok: true}, 200));
      if (u.indexOf("/auth/email/verify-otp") !== -1)
        return Promise.resolve(json({ok: true, email_verified: true}, 200));
      if (u.indexOf("/me") !== -1)
        return Promise.resolve(json(USER, 200));
      if (u.indexOf("/admin/companies") !== -1)
        return Promise.resolve(json([], 200));
      if (u.indexOf("/company/members") !== -1)
        return Promise.resolve(json([], 200));
      // ── project detail / sub-resources ──
      const mDetail = u.match(/\/projects\/([^\/?]+)(\?|$)/);
      if (u.indexOf("/appointments") !== -1) return Promise.resolve(json([], 200));
      if (u.indexOf("/documents") !== -1)    return Promise.resolve(json([], 200));
      if (mDetail && u.indexOf("/projects/") !== -1 && u.indexOf("/projects?") === -1) {
        return Promise.resolve(json(PROJECT_DETAIL, 200));
      }
      // ── projects list (pipeline + directory) ──
      if (u.indexOf("/projects") !== -1) {
        return Promise.resolve(json({
          items: PROJECTS, total: PROJECTS.length, page: 1, total_pages: 1,
          status_counts: STATUS_COUNTS
        }, 200));
      }
      return Promise.resolve(json({}, 200));
    } catch (e) {
      return Promise.resolve(json({error: String(e)}, 200));
    }
  };

  // ── LIFF stub ──
  window.liff = {
    init: () => Promise.resolve(),
    ready: Promise.resolve(),
    isLoggedIn: () => true,
    isInClient: () => true,
    login: () => {},
    logout: () => {},
    getAccessToken: () => "mock-access-token",
    getProfile: () => Promise.resolve({
      userId: "Uxxxxxxxxxxxxxxx", displayName: "สมชาย ใจดี", pictureUrl: ""
    }),
    getDecodedIDToken: () => ({email: "somchai@example.com"}),
    openWindow: () => {},
    closeWindow: () => {},
    getOS: () => "ios",
    getVersion: () => "2.0.0",
  };
})();
"""

PLACEHOLDER_HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>
  html,body{margin:0;height:100%%;font-family:sans-serif}
  .ph{box-sizing:border-box;width:100%%;height:100vh;display:flex;flex-direction:column;
      align-items:center;justify-content:center;gap:14px;
      border:3px dashed #b6b0c8;background:#f7f5fb;color:#6c6482;text-align:center;padding:24px}
  .ic{font-size:64px}
  .t1{font-size:20px;font-weight:700;color:#4b4560}
  .t2{font-size:15px;line-height:1.5;max-width:300px}
  .tag{margin-top:6px;font-size:12px;color:#8a83a0;border:1px solid #cfc9dd;border-radius:999px;padding:4px 12px}
</style></head><body>
<div class="ph"><div class="ic">%(icon)s</div>
<div class="t1">%(title)s</div>
<div class="t2">%(desc)s</div>
<div class="tag">แทรกภาพหน้าจอจริงตรงนี้</div></div>
</body></html>"""


def new_page(browser, scenario, url_file, extra_query=""):
    ctx = browser.new_context(**MOBILE)
    # บล็อกเน็ตภายนอกทั้งหมด (LINE SDK, ฟอนต์ ฯลฯ) เพื่อไม่ให้ค้าง; ไฟล์ในเครื่องปล่อยผ่าน
    ctx.route("**/*", lambda route: (
        route.abort() if route.request.url.startswith(("http://", "https://")) else route.continue_()
    ))
    page = ctx.new_page()
    page.add_init_script("window.__SCN = %r;" % scenario)
    page.add_init_script(INIT_JS)
    page.goto("file://" + url_file + extra_query, wait_until="commit")
    return ctx, page


def seed_session(page):
    page.evaluate("localStorage.setItem('vizzel_token','mock-jwt')")


def shot(page, name, full=True, clip_selector=None):
    path = os.path.join(IMG, name)
    if clip_selector:
        el = page.query_selector(clip_selector)
        if el:
            el.screenshot(path=path)
            print("  ✓", name, "(element)")
            return
    page.screenshot(path=path, full_page=full)
    print("  ✓", name)


# ภาพ Rich Menu (จำลองความละเอียดสูงตามดีไซน์จริงของ Vizzel Track Support — แนวนอน)
# เน้นปุ่ม "Dealer / สำหรับคู่ค้า" ด้วยกรอบแดง + callout ②
RICHMENU_HTML = r"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=1040, initial-scale=1">
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Noto Sans Thai',sans-serif;}
  .wrap{width:1040px;height:700px;position:relative;overflow:hidden;
    background:linear-gradient(118deg,#c6b4f4 0%,#e9e2fb 30%,#ffffff 60%,#e6f5fb 100%);}
  .wrap::before{content:"";position:absolute;inset:0;
    background:radial-gradient(60% 55% at 82% 78%,rgba(46,205,230,.30),transparent 70%);}
  /* top zone */
  .top{position:relative;height:430px;padding:38px 44px;}
  .logo{width:96px;height:96px;border-radius:50%;background:rgba(255,255,255,.6);
    border:1px solid rgba(255,255,255,.9);display:flex;align-items:center;justify-content:center;
    box-shadow:0 6px 20px rgba(90,60,160,.18);}
  .logo img{width:74px;height:74px;object-fit:contain;}
  .plat{display:inline-block;margin-top:20px;font-size:15px;font-weight:700;letter-spacing:3px;
    color:#6a4bd0;border:1.5px solid #b6a4ec;border-radius:24px;padding:7px 18px;background:rgba(255,255,255,.35);}
  .plat b{color:#3ac7e0;}
  h1{margin-top:16px;font-weight:800;line-height:.98;}
  h1 .l1{display:block;font-size:66px;color:#171a3c;}
  h1 .l2{display:block;font-size:66px;
    background:linear-gradient(90deg,#7B3FF2,#12a9d6);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .chips{margin-top:22px;display:flex;gap:10px;}
  .chip{font-size:14px;color:#5b6070;background:rgba(255,255,255,.75);border:1px solid #d7d1ec;
    border-radius:22px;padding:7px 16px;}
  /* dashboard card */
  .dash{position:absolute;right:44px;top:46px;width:556px;background:#0e1730;border-radius:16px;
    padding:16px 18px;box-shadow:0 18px 40px rgba(20,20,60,.28);color:#e7ecf7;}
  .dbar{display:flex;align-items:center;gap:8px;font-size:14px;color:#aeb7cc;letter-spacing:1px;}
  .dot{width:11px;height:11px;border-radius:50%;} .r{background:#ff5f57;}.y{background:#febc2e;}.g{background:#28c840;}
  .live{margin-left:auto;color:#37e0c8;font-weight:700;font-size:13px;letter-spacing:1px;}
  .live b{color:#37e0c8;}
  .tiles{display:flex;gap:12px;margin-top:14px;}
  .tile{flex:1;background:#16203c;border:1px solid #24304f;border-radius:12px;padding:12px 14px;}
  .tile .k{font-size:12px;letter-spacing:2px;color:#8f9ab6;}
  .tile .v{font-size:30px;font-weight:800;color:#fff;margin-top:4px;}
  .tile.hl{border-color:#2aa7d8;background:#132a44;} .tile.hl .v{color:#38b6e6;}
  .chart{margin-top:12px;background:#16203c;border:1px solid #24304f;border-radius:12px;height:120px;padding:6px;}
  .sysline{position:absolute;left:0;right:0;bottom:14px;text-align:center;
    font-size:14px;letter-spacing:5px;color:#8b86a3;font-weight:600;}
  /* bottom buttons */
  .btm{position:absolute;left:0;right:0;bottom:0;height:270px;background:rgba(255,255,255,.72);
    display:flex;border-top:1px solid #ece9f5;}
  .col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;
    position:relative;text-align:center;}
  .col+.col{border-left:1px solid #eceaf3;}
  .col .th{font-size:26px;font-weight:800;color:#1b1e42;line-height:1.15;position:relative;z-index:2;}
  .col .en{font-size:15px;letter-spacing:2px;color:#b9b4cf;font-weight:700;margin-top:-2px;}
  .col .ar{color:#22b7d6;font-size:26px;font-weight:800;}
  .ico{width:64px;height:64px;}
  .col.hot{outline:4px solid #e2352f;outline-offset:-10px;border-radius:14px;background:rgba(255,238,238,.55);}
  .cnum{position:absolute;top:16px;right:22px;width:34px;height:34px;border-radius:50%;
    background:#FFD400;color:#3a2f00;font-weight:800;font-size:19px;
    display:flex;align-items:center;justify-content:center;border:2px solid #e5b800;z-index:3;}
</style></head><body>
  <div class="wrap">
    <div class="top">
      <div class="logo"><img src="../../assets/logo.png"></div>
      <div class="plat"><b>◦</b> INTELLIGENT ASSET PLATFORM</div>
      <h1><span class="l1">แตะเพื่อดู</span><span class="l2">ผลิตภัณฑ์</span></h1>
      <div class="chips"><span class="chip">RFID Tracking</span><span class="chip">Real-time Dashboard</span><span class="chip">Smart Inventory</span></div>
      <div class="dash">
        <div class="dbar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
          &nbsp;VIZZEL · Asset Control<span class="live">● LIVE</span></div>
        <div class="tiles">
          <div class="tile"><div class="k">ASSETS</div><div class="v">12,480</div></div>
          <div class="tile hl"><div class="k">ONLINE</div><div class="v">98.6%</div></div>
          <div class="tile"><div class="k">ALERTS</div><div class="v">03</div></div>
        </div>
        <div class="chart">
          <svg width="100%" height="108" viewBox="0 0 520 108" preserveAspectRatio="none">
            <defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#37cfe8" stop-opacity=".55"/>
              <stop offset="1" stop-color="#37cfe8" stop-opacity="0"/></linearGradient></defs>
            <path d="M0,86 L60,74 L120,80 L180,58 L240,64 L300,42 L360,50 L420,30 L480,40 L520,26 L520,108 L0,108 Z" fill="url(#ar)"/>
            <polyline points="0,86 60,74 120,80 180,58 240,64 300,42 360,50 420,30 480,40 520,26"
              fill="none" stroke="#3fd6ec" stroke-width="3"/>
          </svg>
        </div>
      </div>
      <div class="sysline">VIZZEL · ASSET MANAGEMENT SYSTEM</div>
    </div>
    <div class="btm">
      <div class="col">
        <svg class="ico" viewBox="0 0 64 64" fill="none" stroke="#22b7d6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <rect x="10" y="14" width="44" height="30" rx="8"/><path d="M22 44 L22 54 L34 44"/>
          <circle cx="24" cy="29" r="2.2" fill="#22b7d6" stroke="none"/><circle cx="32" cy="29" r="2.2" fill="#22b7d6" stroke="none"/><circle cx="40" cy="29" r="2.2" fill="#22b7d6" stroke="none"/></svg>
        <div class="th">ติดต่อเจ้า<br>หน้าที่</div><div class="en">TALK TO OUR TEAM</div><div class="ar">&#8595;</div>
      </div>
      <div class="col">
        <svg class="ico" viewBox="0 0 64 64" fill="none" stroke="#8a6ff0" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <path d="M32 56 C32 56 50 40 50 26 A18 18 0 1 0 14 26 C14 40 32 56 32 56 Z"/><circle cx="32" cy="26" r="7"/></svg>
        <div class="th">รายชื่อตัวแทน<br>จำหน่าย</div><div class="en">FIND A DEALER</div><div class="ar">&#8595;</div>
      </div>
      <div class="col hot">
        <div class="cnum">2</div>
        <svg class="ico" viewBox="0 0 64 64" fill="none" stroke="#3aa8ea" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="24" cy="24" r="8"/><circle cx="42" cy="26" r="7"/>
          <path d="M12 50 C12 40 20 36 24 36 C28 36 36 40 36 50"/><path d="M38 49 C38 41 44 38 47 38 C51 38 54 41 54 49"/></svg>
        <div class="th">Dealer</div><div class="en">สำหรับคู่ค้า</div><div class="ar">&#8595;</div>
      </div>
    </div>
  </div>
</body></html>"""


def capture():
    os.makedirs(IMG, exist_ok=True)
    exe = chromium_path()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])

        # 1) SPLASH — ทำให้ liff.init ค้าง เพื่อคงหน้า splash ("กำลังเชื่อมต่อ LINE...")
        try:
            ctx = b.new_context(**MOBILE)
            ctx.route("**/*", lambda route: (
                route.abort() if route.request.url.startswith(("http://", "https://")) else route.continue_()))
            page = ctx.new_page()
            page.add_init_script("window.__SCN = 'splash';")
            page.add_init_script(INIT_JS)
            # override: liff.init ค้างตลอด -> แอปอยู่ที่หน้า splash
            page.add_init_script("window.liff.init = () => new Promise(()=>{});")
            page.goto("file://" + INDEX, wait_until="commit")
            page.wait_for_selector("#splash", state="visible", timeout=8000)
            page.wait_for_timeout(700)
            page.evaluate("""() => {
                const st=document.getElementById('splashStatus');
                if(st) st.textContent='กำลังเชื่อมต่อ LINE...';
            }""")
            shot(page, "01-splash.png", full=False)
            ctx.close()
        except Exception as e:
            print("  ! splash:", e)

        # 2) REGISTER — auth/line ตอบ user_not_found -> showRegister()
        try:
            ctx, page = new_page(b, "register", INDEX)
            page.wait_for_selector("#register", state="visible", timeout=10000)
            page.evaluate("""() => {
                document.getElementById('regFirstName').value='สมชาย';
                document.getElementById('regLastName').value='ใจดี';
                document.getElementById('regPhone').value='0812345678';
                document.getElementById('regEmail').value='somchai@example.com';
                const r=document.getElementById('regRegion'); if(r) r.value='ภาคกลาง';
                document.getElementById('regInviteCode').value='VZ-2026';
                const st=document.getElementById('regInviteStatus');
                if(st){st.textContent='✓ บริษัท วิซเซล อินเทล จำกัด'; st.style.color='#34C759';}
            }""")
            page.wait_for_timeout(300)
            shot(page, "02-register.png")
            ctx.close()
        except Exception as e:
            print("  ! register:", e)

        # 3) EMAIL VERIFY — บังคับแสดงจอยืนยันอีเมล (markup คงที่)
        try:
            ctx, page = new_page(b, "register", INDEX)
            page.wait_for_selector("#register", state="visible", timeout=10000)
            page.evaluate("""() => {
                for (const id of ['splash','register','app']) {
                    const el=document.getElementById(id); if(el) el.style.display='none';
                }
                const ev=document.getElementById('emailVerify'); if(ev) ev.style.display='block';
                const inp=document.getElementById('verifyEmailInput'); if(inp) inp.value='somchai@example.com';
                const otp=document.getElementById('verifyOtpInput'); if(otp) otp.value='123456';
                const h=document.getElementById('verifyHint');
                if(h) h.textContent='ส่งรหัสไปที่อีเมลแล้ว — กรอกรหัส 6 หลักภายใน 10 นาที';
            }""")
            page.wait_for_timeout(200)
            shot(page, "03-email-verify.png")
            ctx.close()
        except Exception as e:
            print("  ! email-verify:", e)

        # 4) MAIN APP + PIPELINE — seed session -> boot ตรงเข้า app
        try:
            ctx = b.new_context(**MOBILE)
            ctx.route("**/*", lambda route: (
                route.abort() if route.request.url.startswith(("http://", "https://")) else route.continue_()))
            page = ctx.new_page()
            page.add_init_script("window.__SCN = 'app';")
            page.add_init_script(INIT_JS)
            page.add_init_script("localStorage.setItem('vizzel_token','mock-jwt');")
            page.goto("file://" + INDEX, wait_until="commit")
            page.wait_for_selector("#app", state="visible", timeout=12000)
            page.wait_for_selector("#pipeGrid .pipe-card", timeout=12000)
            page.wait_for_timeout(600)
            shot(page, "04-main-pipeline.png")

            # 5) PROFILE MENU — เปิด dropdown
            try:
                page.evaluate("""() => {
                    const d=document.getElementById('profileDropdown'); if(d) d.style.display='block';
                    for (const id of ['menuMembers','menuCompany']) {
                        const el=document.getElementById(id); if(el) el.style.display='block';
                    }
                }""")
                page.wait_for_timeout(200)
                shot(page, "05-profile-menu.png", full=False)
                page.evaluate("document.getElementById('profileDropdown').style.display='none'")
            except Exception as e:
                print("  ! profile-menu:", e)

            # 6) PROJECTS directory tab
            try:
                page.evaluate("showTab('projects')")
                page.wait_for_timeout(700)
                shot(page, "06-projects-directory.png")
            except Exception as e:
                print("  ! projects-dir:", e)

            # 7) CREATE PROJECT modal
            try:
                page.evaluate("openCreateModal()")
                page.wait_for_timeout(400)
                page.evaluate("""() => {
                    const set=(id,v)=>{const e=document.getElementById(id); if(e) e.value=v;};
                    set('newAgencyName','องค์การบริหารส่วนตำบลหนองแวง');
                    set('newAgencyType','องค์การบริหารส่วนตำบล');
                    set('newProvince','มหาสารคาม');
                    set('newContactName','นางสาวสุดา ทำดี');
                    set('newContactPosition','นักวิชาการพัสดุ');
                    set('newPhone','0812345678');
                }""")
                page.wait_for_timeout(200)
                shot(page, "07-create-project.png")
                page.evaluate("try{closeCreateModal()}catch(e){}")
            except Exception as e:
                print("  ! create-modal:", e)

            # 8) PROJECT DETAIL — info tab
            try:
                page.evaluate("showDetail('p-1')")
                page.wait_for_selector("#detailContent .detail-tabs", timeout=10000)
                page.wait_for_timeout(600)
                page.evaluate("switchDetailTab('info')")
                page.wait_for_timeout(400)
                shot(page, "08-detail-info.png")
            except Exception as e:
                print("  ! detail-info:", e)

            # 9) STATUS / DOCUMENT stage tab (อัพเดทงาน)
            try:
                page.evaluate("switchDetailTab('work')")
                page.wait_for_timeout(500)
                shot(page, "09-detail-work-docs.png")
            except Exception as e:
                print("  ! detail-work:", e)

            # 10) APPOINTMENT add form
            try:
                page.evaluate("switchDetailTab('appt')")
                page.wait_for_timeout(400)
                page.evaluate("try{toggleActionPanel('appt-add-present','appt-arrow-present')}catch(e){}")
                page.wait_for_timeout(200)
                page.evaluate("""() => {
                    const t=document.getElementById('ap-present-type');
                    if(t){t.value='online'; try{togglePresentMeetOptions()}catch(e){}}
                }""")
                page.wait_for_timeout(300)
                shot(page, "10-appointment-form.png")
            except Exception as e:
                print("  ! appointment:", e)

            ctx.close()
        except Exception as e:
            print("  ! main app:", e)

        # 11) UPLOAD page
        try:
            ctx = b.new_context(**MOBILE)
            ctx.route("**/*", lambda route: (
                route.abort() if route.request.url.startswith(("http://", "https://")) else route.continue_()))
            page = ctx.new_page()
            page.add_init_script(INIT_JS)
            page.goto("file://" + UPLOAD + "?project_id=p-1&token=mock-jwt&doc_type=tor_support",
                      wait_until="commit")
            page.wait_for_timeout(800)
            shot(page, "11-upload.png")
            ctx.close()
        except Exception as e:
            print("  ! upload:", e)

        # ── 00b) Rich Menu mock (หน้าต้อนรับ LINE OA + Rich Menu, เน้นปุ่ม "สำหรับคู่ค้า") ──
        try:
            ctx = b.new_context(**MOBILE)
            page = ctx.new_page()
            page.set_content(RICHMENU_HTML.replace("../../assets/logo.png", logo_data_uri()))
            page.wait_for_timeout(250)
            shot(page, "00b-line-richmenu.png", clip_selector=".wrap")
            ctx.close()
        except Exception as e:
            print("  ! richmenu:", e)

        b.close()

    # ── 00a) QR code เพิ่มเพื่อน LINE (สร้างจากลิงก์จริง — คมชัด) ──
    make_qr(LINE_ADD_FRIEND_URL, os.path.join(IMG, "00a-line-qr.png"))
    trim_images()
    print("capture เสร็จสิ้น -> images/")


LINE_ADD_FRIEND_URL = "https://lin.ee/UAOQyx0"


def make_qr(data, out):
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=16, border=3)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(out)
        print("  ✓ 00a-line-qr.png (QR:", data + ")")
    except Exception as e:
        print("  ! qr:", e)


def trim_images():
    """ตัดขอบขาวส่วนเกิน (ล่าง/ซ้าย/ขวา) ให้ภาพดูเป็นระเบียบ — คงขอบบน (header) ไว้"""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("  (ข้าม trim: ไม่มี Pillow)"); return
    skip = ("00a-line-qr", "00b-line-richmenu")  # คง quiet-zone ของ QR และเฟรมมือถือของ Rich Menu ไว้
    for fn in glob.glob(os.path.join(IMG, "*.png")):
        if any(s in os.path.basename(fn) for s in skip):
            continue
        try:
            im = Image.open(fn).convert("RGB")
            diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
            bbox = diff.getbbox()
            if not bbox:
                continue
            l, t, r, btm = bbox
            pad = 24
            im.crop((max(0, l - pad), 0, min(im.width, r + pad), min(im.height, btm + pad))).save(fn)
        except Exception as e:
            print("  ! trim", os.path.basename(fn), e)


def render():
    if not os.path.exists(MANUAL):
        print("ไม่พบ manual.html — ข้าม render"); return
    exe = chromium_path()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
        page = b.new_page()
        page.goto("file://" + MANUAL, wait_until="networkidle")
        page.wait_for_timeout(800)
        page.pdf(path=PDF_OUT, format="A4", print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                 prefer_css_page_size=True)
        b.close()
    print("render เสร็จสิ้น ->", os.path.basename(PDF_OUT))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "capture"):
        capture()
    if mode in ("all", "render"):
        render()

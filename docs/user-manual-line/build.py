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


# mock หน้าจอ LINE OA + Rich Menu (อ้างอิงหน้าจอจริงของ Vizzel Track Support)
RICHMENU_HTML = r"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=390, initial-scale=1">
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Noto Sans Thai','Sarabun',sans-serif;}
  body{width:390px;background:#28344c;position:relative;color:#fff;}
  .bar{display:flex;align-items:center;gap:8px;padding:12px 12px 10px;background:#28344c;}
  .bk{font-size:20px;color:#cfd6e4;}
  .oa-av{width:34px;height:34px;border-radius:50%;background:#fff;display:flex;align-items:center;
        justify-content:center;font-size:9px;font-weight:700;color:#2b3a86;overflow:hidden;}
  .oa-av img{width:100%;height:100%;object-fit:contain;}
  .oa-t{flex:1;line-height:1.2;}
  .oa-t b{font-size:16px;} .oa-t span{font-size:11px;color:#aeb6c6;}
  .oa-ic{color:#cfd6e4;font-size:17px;margin-left:9px;}
  .warn{display:flex;gap:8px;align-items:flex-start;background:#2f3c57;color:#d7deec;
        font-size:11.5px;line-height:1.35;padding:10px 12px;}
  .warn .x{margin-left:auto;color:#9aa4ba;}
  .datechip{width:max-content;margin:14px auto 12px;
        background:#3a465f;color:#cfd6e4;font-size:12px;padding:4px 14px;border-radius:20px;}
  .msg{display:flex;gap:8px;padding:0 12px;align-items:flex-end;}
  .msg .av{width:30px;height:30px;border-radius:50%;background:#fff;flex:0 0 auto;overflow:hidden;
        display:flex;align-items:center;justify-content:center;}
  .msg .av img{width:100%;height:100%;object-fit:contain;}
  .bub{background:#FBF7DE;color:#333;border-radius:4px 16px 16px 16px;padding:11px 13px;
       font-size:13.5px;line-height:1.5;max-width:250px;white-space:pre-line;position:relative;}
  .tm{align-self:flex-end;font-size:10px;color:#9aa4ba;margin-left:4px;}
  /* Rich menu */
  .rm{margin-top:70px;height:300px;background:#fff;
      border-top:1px solid #dfe3ea;display:flex;flex-direction:column;}
  .rm-ban{flex:0 0 118px;background:linear-gradient(135deg,#efeafc,#e6f3fb);
      position:relative;padding:16px 16px 0;overflow:hidden;}
  .rm-ban h3{font-size:23px;font-weight:800;color:#3a2e6e;}
  .rm-ban h3 em{color:#1a9bd7;font-style:normal;}
  .chips{display:flex;gap:6px;margin-top:12px;}
  .chip{font-size:9px;color:#6b6f86;background:#fff;border:1px solid #d8d3ec;border-radius:20px;padding:3px 9px;}
  .rm-row{flex:1;display:flex;}
  .rm-b{flex:1;border-right:1px dashed #e5e5ea;display:flex;flex-direction:column;
        align-items:center;justify-content:center;gap:8px;text-align:center;position:relative;}
  .rm-b:last-child{border-right:none;}
  .rm-ic{font-size:30px;}
  .rm-b .lb{font-size:14px;font-weight:700;color:#e0559b;line-height:1.25;}
  .rm-b.p2 .lb{color:#7b4fd0;} .rm-b.p3 .lb{color:#2f8fd6;}
  .rm-ar{color:#b7b2c6;font-size:15px;}
  .hot{outline:3px solid #e2352f;outline-offset:-3px;border-radius:6px;background:#fff5f5;}
  .cnum{position:absolute;top:6px;right:8px;width:24px;height:24px;border-radius:50%;
        background:#FFD400;color:#3a2f00;font-weight:800;font-size:13px;
        display:flex;align-items:center;justify-content:center;border:1px solid #e5b800;}
  .inbar{height:44px;background:#fff;border-top:1px solid #e5e8ee;position:relative;
         display:flex;align-items:center;justify-content:center;gap:8px;color:#6b7180;font-size:14px;}
  .kb{position:absolute;left:12px;font-size:16px;color:#9aa2b2;}
</style></head><body>
  <div class="bar">
    <span class="bk">&#8249;</span>
    <div class="oa-av"><img src="../../assets/logo.png"></div>
    <div class="oa-t"><b>Vizzel Track Support</b><br><span>ผู้รับผิดชอบเป็นผู้ตอบกลับ</span></div>
    <span class="oa-ic">&#9906;</span><span class="oa-ic">&#9776;</span>
  </div>
  <div class="warn"><span>&#9650;</span>
    <span>บัญชีนี้ไม่ได้เป็นบัญชีรับรอง โปรดตรวจสอบให้มั่นใจก่อนให้ข้อมูลส่วนบุคคลหรือทำธุรกรรมใดๆ</span>
    <span class="x">&#10005;</span></div>
  <div class="datechip">พ. 20 พ.ค.</div>
  <div class="msg">
    <div class="av"><img src="../../assets/logo.png"></div>
    <div class="bub">สวัสดี คุณ B.
นี่คือบัญชีทางการของ Vizzel Track Support
ขอบคุณที่เป็นเพื่อนกับเรา🎉

เราจะส่งข่าวสารล่าสุดผ่านบัญชีทางการนี้เป็นระยะ✉️
เตรียมรับได้เลย!🎁</div>
    <span class="tm">02:51</span>
  </div>
  <div class="rm">
    <div class="rm-ban">
      <h3>แตะเพื่อดู <em>ผลิตภัณฑ์</em></h3>
      <div class="chips"><span class="chip">RFID Tracking</span><span class="chip">Real-time Dashboard</span><span class="chip">Smart Inventory</span></div>
    </div>
    <div class="rm-row">
      <div class="rm-b p1"><div class="rm-ic">💬</div><div class="lb">ติดต่อ<br>เจ้าหน้าที่</div><div class="rm-ar">&#10142;</div></div>
      <div class="rm-b p2"><div class="rm-ic">📍</div><div class="lb">รายชื่อ<br>ตัวแทนจำหน่าย</div><div class="rm-ar">&#10142;</div></div>
      <div class="rm-b p3 hot"><div class="cnum">2</div><div class="rm-ic">👥</div><div class="lb">สำหรับคู่ค้า</div><div class="rm-ar">&#10142;</div></div>
    </div>
  </div>
  <div class="inbar"><span class="kb">&#9000;</span>เมนู ▾</div>
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
            logo = os.path.join(REPO, "assets", "logo.png")
            page.set_content(RICHMENU_HTML.replace("../../assets/logo.png", "file://" + logo))
            page.wait_for_timeout(200)
            shot(page, "00b-line-richmenu.png", full=True)
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

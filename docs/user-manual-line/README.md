# คู่มือการเข้าใช้งานระบบ Vizzel Sales ผ่าน LINE

คู่มือประกอบการใช้งาน (User Manual) สำหรับผู้ใช้ปลายทางที่เข้าใช้งานระบบ **Vizzel Sales** ผ่าน **LINE (LIFF)**
รูปเล่ม/เลย์เอาต์อ้างอิงตามคู่มือแบบราชการ และเนื้อหาทุกส่วน **อ้างอิงจากโค้ดจริง** ของ
`vizzel-sales-frontend` (index.html / upload.html) และ backend `vizzel-sales`

## ไฟล์ในโฟลเดอร์นี้
| ไฟล์ | รายละเอียด |
|------|-----------|
| `Vizzel-Sales-LINE-User-Manual.pdf` | **ไฟล์คู่มือฉบับสมบูรณ์** (A4, 13 หน้า) — ไฟล์ที่ส่งมอบ |
| `manual.html` | เทมเพลตคู่มือ (ฝังฟอนต์ TH Sarabun, header/footer, สารบัญ, flowchart, ทุกขั้นตอน) |
| `build.py` | สคริปต์สร้างคู่มือ: ถ่ายภาพหน้าจอ (Playwright) + render เป็น PDF |
| `images/` | ภาพหน้าจอ (ถ่ายอัตโนมัติที่ความละเอียดหน้าจอมือถือ 390×844 @2x) |
| `fonts/` | ฟอนต์ **TH Sarabun New** (.ttf) ที่ฝังในคู่มือ |

## วิธี re-build คู่มือ
ต้องมี Chromium (มากับ environment ที่ `/opt/pw-browsers`) — ไม่ต้องรัน `playwright install`

```bash
pip install playwright pillow      # ครั้งแรกครั้งเดียว
cd docs/user-manual-line

python3 build.py            # ถ่ายภาพหน้าจอใหม่ + render PDF (ทั้งหมด)
python3 build.py capture    # เฉพาะถ่ายภาพหน้าจอ -> images/
python3 build.py render     # เฉพาะ render manual.html -> PDF
```

`build.py` จะ stub LIFF + mock API แล้วขับ SPA ไปถ่ายภาพแต่ละหน้าจอจริง จากนั้นตัดขอบขาวส่วนเกินให้เป็นระเบียบ

## หมายเหตุ / สิ่งที่ควรปรับก่อนเผยแพร่
1. **ฟอนต์:** ผู้ใช้ระบุ “TH Sarabun **TSK**” แต่ไฟล์ TSK ไม่มีเผยแพร่สาธารณะแยกต่างหาก
   จึงใช้ **TH Sarabun New** (ฉบับทางการ SIPA/dip-sipa) ซึ่งเป็นฟอนต์ตระกูลเดียวกันและหน้าตาแทบเหมือนกัน
   หากมีไฟล์ TSK จริง ให้วางทับใน `fonts/` (ตั้งชื่อ `THSarabunNew*.ttf`) แล้ว `python3 build.py render` ใหม่
2. **ภาพขั้นตอนฝั่ง LINE:**
   - `00a-line-qr.png` = QR เพิ่มเพื่อน สร้างจากลิงก์ `https://lin.ee/UAOQyx0` ด้วย lib `qrcode` (ต้อง `pip install qrcode`)
     — หากเปลี่ยนลิงก์ ให้แก้ค่า `LINE_ADD_FRIEND_URL` ใน `build.py` แล้ว `python3 build.py capture`
   - `00b-line-richmenu.png` = **ภาพ Rich Menu จริง** (ต้นฉบับ `src/richmenu-real.png` 2500×1686 จากผู้ใช้)
     โดย `build.py` วาด **กรอบแดง + callout ②** ทับปุ่ม Dealer/สำหรับคู่ค้าอัตโนมัติ (`make_richmenu()`)
     — ถ้าไม่มี `src/richmenu-real.png` จะ fallback เป็นภาพจำลอง HTML (`RICHMENU_HTML`)
     — เปลี่ยนภาพจริงได้โดยวางไฟล์ใหม่ทับ `src/richmenu-real.png` แล้ว `python3 build.py render`
     (ปรับตำแหน่งกรอบแดงได้ที่พิกัดสัดส่วนใน `make_richmenu()`)
3. **ข้อความลิขสิทธิ์ท้ายหน้า** ใช้บรรทัดกลาง ๆ (“สงวนลิขสิทธิ์ © บริษัท วิซเซล อินเทล จำกัด”) — ปรับได้ที่ `manual.html`

## โครงสร้างเนื้อหา (13 หน้า)
หน้าปก · สารบัญ · สรุปขั้นตอน (flowchart) · แล้วตามด้วยรายละเอียด 10 ส่วน:
เข้าสู่ระบบผ่าน LINE · ลงทะเบียน+Invite Code · ยืนยันอีเมล (OTP) · แนะนำเมนูหลัก ·
สร้าง/กรอกโครงการ · อัปเดตสถานะ+แนบเอกสารตามขั้น · ลงนัดหมาย · แนบไฟล์เอกสาร ·
ข้อห้าม/ข้อควรระวัง · ออกจากระบบ

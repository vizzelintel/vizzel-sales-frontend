# อีเมลส่งคู่มือให้คู่ค้า (Dealer)

ชุดไฟล์สำหรับส่งคู่มือ `Vizzel-Sales-LINE-User-Manual.pdf` ให้คู่ค้าทางอีเมล

| ไฟล์ | ใช้ทำอะไร |
|------|-----------|
| `dealer-email.txt` | **อีเมลสำเร็จรูป** (หัวข้อ + เนื้อหา ข้อความล้วน) — คัดลอกวาง Gmail/Outlook ได้เลย |
| `dealer-email.html` | **เทมเพลตอีเมล HTML** แบบมีดีไซน์ (โลโก้ + QR + ปุ่ม) โหลดรูปจาก GitHub Pages อัตโนมัติ |
| `prompt-th.txt` | **Prompt** สำหรับให้ AI (Claude/Gemini) ร่างอีเมลให้เอง |
| `preview.png` | ภาพตัวอย่างหน้าตาอีเมล HTML |

## วิธีส่ง (ง่ายสุด)
1. เปิด `dealer-email.txt` → เลือกหัวข้อ 1 แบบ คัดลอกเนื้อหาไปวางใน Gmail
2. เติมข้อมูลในวงเล็บ `[...]` (Invite Code, เบอร์ติดต่อ, อีเมลบริษัท)
3. **แนบไฟล์** `Vizzel-Sales-LINE-User-Manual.pdf`
4. กดส่ง

## ใช้เทมเพลต HTML (สวยกว่า)
- คัดลอกทั้งไฟล์ `dealer-email.html` ไปวางในโหมด HTML ของโปรแกรมส่งอีเมล
- รูปโลโก้/QR โหลดจาก GitHub Pages อัตโนมัติ (ต้องเผยแพร่ Pages ของ repo แล้ว):
  - โลโก้: `https://vizzelintel.github.io/vizzel-sales-frontend/assets/logo.png`
  - QR: `https://vizzelintel.github.io/vizzel-sales-frontend/docs/user-manual-line/images/00a-line-qr.png`
- แก้ค่าในวงเล็บ `[...]` ให้เป็นข้อมูลบริษัท

## ใช้ผ่าน AI
วาง `prompt-th.txt` ให้ Claude/Gemini แล้วให้ช่วยร่าง/ปรับสำนวนได้ตามต้องการ

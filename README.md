# คู่มือการใช้งาน Docker สำหรับโปรเจกต์ LaTeX (CS KKU Project)

คู่มือนี้แนะนำการคอมไพล์เอกสารรายงาน/วิทยานิพนธ์ (LaTeX / XeLaTeX) ด้วย **Docker** โดยไม่จำเป็นต้องติดตั้ง TeX Live หรือ XeLaTeX บนเครื่องของคุณเอง

---

## 🚀 ความต้องการเบื้องต้น (Prerequisites)

- ติดตั้ง **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (เปิดใช้งานและพร้อมใช้งาน)

---

## 🛠️ วิธีการใช้งาน (Usage)

### 1. คอมไพล์เอกสารเป็น PDF (Build PDF)

เปิด Terminal / PowerShell / Command Prompt ในโฟลเดอร์โปรเจกต์ แล้วเลือกใช้คำสั่งใดคำสั่งหนึ่งด้านล่าง:

#### ใช้ Docker Compose (แนะนำ):
```bash
docker compose run --rm latex
```
หรือรัน:
```bash
docker compose up
```

#### ใช้ Script (บน Windows):
- **Command Prompt (CMD):**
  ```cmd
  build.bat
  ```
  *(หรือดับเบิลคลิกไฟล์ `build.bat` ได้โดยตรง)*
- **PowerShell:**
  ```powershell
  .\build.ps1
  ```

#### ใช้ Docker CLI ปกติ (ไม่ผ่าน Compose):
```bash
# Windows PowerShell
docker run --rm -v ${PWD}:/workspace cskku-latex:latest latexmk main.tex

# Windows CMD
docker run --rm -v "%cd%":/workspace cskku-latex:latest latexmk main.tex

# Linux / macOS
docker run --rm -v $(pwd):/workspace cskku-latex:latest latexmk main.tex
```

เอกสาร PDF ที่ได้จะอยู่ที่ไฟล์ `main.pdf` ในโฟลเดอร์นี้ทันที

---

### 2. โหมด Auto-recompile เมื่อบันทึกไฟล์ (Watch Mode)

เหมาะสำหรับการเขียนเนื้อหา เมื่อกด Save ในไฟล์ `.tex` ระบบจะคอมไพล์ PDF ใหม่อัตโนมัติ:

```bash
docker compose run --rm watch
```
หรือ
```cmd
build.bat watch
```
*(กด `Ctrl + C` เพื่อหยุดการทำงาน)*

---

### 3. ล้างไฟล์ชั่วคราว (Clean Temp/Cache Files)

ลบไฟล์แคชและไฟล์ auxiliary ต่างๆ เช่น `.aux`, `.log`, `.toc`, `.out`, `.bbl` ฯลฯ:

```bash
docker compose run --rm clean
```
หรือ
```cmd
build.bat clean
```

---

### 4. เข้าไปใน Shell ของ Container (Debug)

หากต้องการรันคำสั่งด้วยตนเองภายใน Container:

```bash
docker compose run --rm latex bash
```
หรือ
```cmd
build.bat shell
```

---

## 📁 โครงสร้างไฟล์ Docker ที่เพิ่มเข้ามา

| ไฟล์ | หน้าที่ |
| :--- | :--- |
| `Dockerfile` | Image configuration ใช้ TeX Live พร้อม XeLaTeX และฟอนต์ไทย |
| `docker-compose.yml` | คำสั่ง Compose สำเร็จรูปสำหรับ `latex` (build), `watch`, `clean` |
| `.dockerignore` | รายการไฟล์ที่มองข้ามเวลาสร้าง Docker image เพื่อความรวดเร็ว |
| `.gitignore` | รายการไฟล์ที่ไม่ต้องนำขึ้น Git (ไฟล์ชั่วคราวจากการคอมไพล์) |
| `build.bat` | Script สำเร็จรูปสำหรับผู้ใช้ Windows CMD (ดับเบิลคลิกได้) |
| `build.ps1` | Script สำเร็จรูปสำหรับ PowerShell |
| `Makefile` | คำสั่งสำหรับ Make (Linux/macOS) |

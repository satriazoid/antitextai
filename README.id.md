# antitextai

Bersihkan jejak AI dari teks dan kode hasil LLM: karakter tak terlihat, tanda kutip melengkung,
banner pemisah, penanda akhir blok, kalimat pembuka gaya obrolan, indentasi NBSP.

Satu paket Python kecil. Tanpa dependensi, tanpa jaringan, tanpa API key.

[![CI](https://github.com/satriazoid/antitextai/actions/workflows/ci.yml/badge.svg)](https://github.com/satriazoid/antitextai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English README](README.md)

Repositori ini berisi dua hal yang selalu dijaga sinkron:

| Bagian | Isinya |
| --- | --- |
| `antitextai/` | Paket Python dan CLI yang menjalankan bagian mekanis dari aturan |
| `SKILL.md` | Skill sesuai standar [Agent Skills](https://agentskills.io), sehingga Claude Code, opencode, Cursor, Copilot, Codex, Windsurf, Cline, Aider, Hermes, omp dan lainnya tahu cara memakainya, termasuk keputusan yang tidak bisa diambil regex |

## Kenapa ada

Keluaran model punya sidik jari, dan sidik jari itu ikut terkirim ke commit, dokumen, dan pull
request:

- Zero-width space dan BOM di awal file hasil salin dari UI chat.
- `“tanda kutip melengkung”` dan `…` di dalam file sumber, yang merusak string literal dan skrip shell.
- Banner `# ======================================` dan penanda `# end of function add`.
- `Certainly! Here is the complete breakdown:` sebelum isi yang sebenarnya.
- Non-breaking space di dalam indentasi, yang bikin `IndentationError` di Python.

Semua itu mekanis. Program harus menanganinya dengan cara yang sama setiap kali, dan harus bisa
membuktikan file sudah bersih. Itulah isi repositori ini.

Bagian yang butuh pertimbangan tetap milik Anda: apakah sebuah docstring membawa kontrak, apakah
tanda hubung menghubungkan rentang angka atau anak kalimat, apakah banner menandai batas modul
yang nyata. Alat ini melaporkan hal itu dan menolak menebak.

## Yang dibuang, dan yang ditolak disentuh

| Dibuang atau dinormalkan | Jadi |
| --- | --- |
| `U+200B/200C/200D/2060/FEFF/00AD/200E/200F` (zero width, BOM di tengah file, soft hyphen, penanda bidi) | dihapus |
| `U+00A0`, `U+202F` (spasi tak terpisah) | spasi biasa |
| `U+201C/201D/2018/2019`, `U+2032/2033` (kutip melengkung, prime) | `"` dan `'` |
| `U+2026` (elipsis satu karakter) | `...` |
| `U+00D7`, `U+2212` di prosa dan komentar | `x`, `-` |
| Bullet `U+2022` | `-` (`- ` di awal baris) |
| Baris banner `# ====...` dan `// ----...` | dihapus |
| `# end of loop`, `// end function f`, termasuk yang menempel di akhir baris kode | dihapus, kodenya tetap |
| Komentar narasi `# Step 1: ...`, `# now, we ...`, `# Return the result` | dihapus |
| Pembuka `Certainly!`, `Sure thing!`, `No problem!` | kerangkanya dibuang, kalimatnya tetap dan huruf pertamanya dinaikkan |
| Pembuka `In today's ... , ...`, `Overall, ...`, `That said, ...` | kerangka dibuang, anak kalimatnya tetap |
| `It's important to note that ...`, `Note that ...` (di awal baris atau tengah paragraf) | kerangka dibuang, isinya tetap |
| `Here is the complete Python script to achieve this:` sebelum blok kode | dihapus |
| `Hope this helps!`, `Let me know if ...` sebagai penutup | dihapus, kalimat sebelumnya tetap |
| Spasi di akhir baris, tiga baris kosong berurutan atau lebih | dirapikan |

Sengaja dipertahankan:

| Dipertahankan | Alasannya |
| --- | --- |
| Em dash `U+2014`, en dash `U+2013` | Satu tanda hubung bisa menghubungkan rentang angka (`2019–2021`), nama majemuk (`Jean–Luc`), kutipan, atau anak kalimat. Setiap kasus punya pengganti berbeda, jadi **setiap kemunculan dilaporkan untuk ditinjau, tidak pernah diganti otomatis.** |
| Simbol matematika: `Σ Π λ ± × ≥` dan huruf Yunani lain di rumus | Itu isi, bukan hiasan. |
| Latin beraksen, Kiril, Ibrani, Arab, CJK | Tulisan sungguhan. Pemindai menandainya `keep`. |
| Frontmatter YAML | Dipisahkan sebelum aturan baris, jadi pembatas `---` dan byte frontmatter aman. |
| Heading setext (`Judul` di atas `------`) | Deretan tanda hubung di bawah baris teks adalah heading, bukan banner. |
| String literal yang mirip komentar | `x = "# end of loop"` dan `url = 'http://x--y/z'` punya tes dan tidak berubah sedikit pun. |
| Akhir baris | CRLF masuk, CRLF keluar. LF masuk, LF keluar. |

## Instalasi

```bash
# 1. Clone dan langsung pakai. Tidak perlu instalasi apa pun, paketnya ada di akar repo.
git clone https://github.com/satriazoid/antitextai.git
cd antitextai
python -m antitextai scan .

# 2. Pasang CLI-nya secara terpisah (paling nyaman untuk pemakaian harian).
pipx install "git+https://github.com/satriazoid/antitextai"
# atau dengan uv:
uv tool install "git+https://github.com/satriazoid/antitextai"

# 3. Instalasi editable kalau mau mengubah kodenya sambil memakai library-nya.
python -m venv .venv
.venv/Scripts/python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux dan macOS
```

Butuh Python 3.9 atau lebih baru (CI menguji 3.9, 3.12, dan 3.13 di Linux, macOS, dan Windows).
Tanpa dependensi runtime.

## Mulai cepat

```bash
python -m antitextai scan .                    # 1. inventaris, tidak mengubah apa pun
python -m antitextai clean --write README.md   # 2. tulis ulang di tempat
python -m antitextai verify . --strict         # 3. buktikan bersih, keluar 1 kalau belum
```

`scan` melaporkan, `clean` menulis ulang, `verify` membuktikan. Jalankan berurutan.

Contoh keluaran nyata, dari `examples/demo_before.md`:

```text
$ python -m antitextai scan examples/demo_before.md
examples\demo_before.md
    U+00A0 x2    mapped       first 16:8     NO-BREAK SPACE
    U+200B x1    mapped       first 31:7     ZERO WIDTH SPACE
    U+2013 x1    review       first 30:32    EN DASH
    U+2014 x2    review       first 30:8     EM DASH
    rule INTERJECT       x1   lines 6  'Certainly! H'
    rule CLAUSE          x1   lines 8  "In today's fast-paced digital landscape, t"
    rule SEPARATOR       x2   lines 19,21  '# ==========================================\n'

1 of 1 files carry AI tells: 15 non-ASCII characters (3 need review), 15 rule hits
```

Isi `examples/` adalah alat uji yang disengaja kotor, dan `examples/demo_after.md` adalah hasil
persis dari pembersihannya. `tests/test_examples.py` gagal kalau keduanya mulai berbeda.

## Memakai dari agent lain

Agent yang bisa menjalankan perintah shell bisa memakai CLI-nya. Agent yang membaca `SKILL.md`
atau `AGENTS.md` langsung mengerti aturannya, cukup dari hasil clone.

```bash
mkdir -p ~/.claude/skills/antitextai && cp SKILL.md ~/.claude/skills/antitextai/   # Claude Code
mkdir -p .opencode/skills/antitextai && cp SKILL.md .opencode/skills/antitextai/   # opencode (proyek)

# Atau pakai installer, yang sudah tahu path sepuluh tool:
bash scripts/install.sh --target claude-code,opencode,cursor,copilot,codex,gemini,hermes
pwsh scripts/install.ps1 -Target claude-code,opencode,cursor,copilot,codex,gemini,hermes
```

| Tool | Letak skill atau aturannya |
| --- | --- |
| Claude Code | `.claude/skills/antitextai/SKILL.md` (proyek) atau `~/.claude/skills/antitextai/SKILL.md` (global) |
| opencode | `.opencode/skills/antitextai/SKILL.md`, juga membaca `.claude/skills/` dan `.agents/skills/` |
| Codex CLI dan pembaca `AGENTS.md` lain | `AGENTS.md` di akar repo, `~/.codex/AGENTS.md` untuk global |
| GitHub Copilot | `.github/copilot-instructions.md`, versi per-path di `.github/instructions/*.instructions.md` |
| Cursor | `.cursor/rules/antitextai.mdc`, atau `AGENTS.md` |
| Windsurf | `.windsurf/rules/antitextai.md` |
| Cline | `.clinerules/antitextai.md` |
| Aider | `CONVENTIONS.md` |
| Gemini CLI | `GEMINI.md` di akar proyek, atau `~/.gemini/GEMINI.md` |
| Hermes Agent | `~/.hermes/skills/antitextai/SKILL.md`, di Windows `%LOCALAPPDATA%\hermes\skills\` |
| omp (oh-my-pi) | `.omp/skills/antitextai/SKILL.md` di proyek |

File siap salin untuk semua tool di atas ada di folder [`integrations/`](integrations), dan
[`docs/agent-integration.md`](docs/agent-integration.md) menjelaskan pemasangan plus prompt agar
agent memakai alat ini dengan cara yang sama setiap kali.

## Dipakai sebagai library

```python
from antitextai import clean, assert_no_artifacts, scan_text

text = open("draft.md", encoding="utf-8").read()

print(scan_text(text)["review"])        # em/en dash yang perlu ditinjau, sebelum apa pun diubah
bersih = clean(text)                    # hanya pass mekanis
assert_no_artifacts(bersih)             # melempar AssertionError berisi sisa, atau mengembalikan None
```

| Fungsi | Kegunaan |
| --- | --- |
| `clean(text, strip_bom=True)` | Menjalankan semua pass deterministik, mengembalikan teks baru, tanpa I/O. |
| `assert_no_artifacts(text)` | Melempar kalau masih ada jejak. Aturan yang sama dengan pembersihnya, jadi tidak mungkin berbeda pendapat. |
| `scan_text(text)` / `scan_paths(paths)` | Inventaris: jumlah per codepoint, lokasi pertama, klasifikasi, dan hit per aturan. |
| `verify_text(text)` / `verify_paths(paths)` | Pass pembuktian, plus catatan selama em/en dash belum ditinjau. |

## Referensi CLI

```text
antitextai scan   PATH... [--strict] [--json] [--ext .md] [--exclude GLOB]
antitextai clean  PATH... [--write] [--no-bom] [--quiet]
antitextai verify PATH... [--strict] [--allow-dashes] [--show-clean]
```

- `PATH` boleh file atau direktori. `-` membaca stdin dan menulis stdout (khusus `clean`).
- Direktori ditelusuri rekursif, difilter ke ekstensi teks yang dikenal, dan melewati `.git`,
  `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, `target`. File yang disebut langsung di
  command line selalu diproses, apa pun ekstensinya.
- File biner (ada byte NUL) dan file yang bukan UTF-8 dilewati, bukan dirusak.
- `clean` tanpa `--write` hanya mencetak hasilnya dan tidak menyentuh file, jadi aman.
- Kode keluar: `0` sukses, `1` ada temuan atau sisa, `2` salah pemakaian. `--strict` mengubah
  laporan menjadi kegagalan, yang dibutuhkan langkah CI.

Contoh langkah CI:

```yaml
- name: Tidak ada jejak AI
  run: python -m antitextai verify . --strict --exclude "examples/**" --exclude "tests/**"
```

pre-commit:

```yaml
repos:
  - repo: https://github.com/satriazoid/antitextai
    rev: v1.0.0
    hooks:
      - id: antitextai
```

## Keputusan desain

1. **Em dan en dash tidak pernah diganti otomatis.** Penggantinya bergantung pada makna.
2. **Kerangka dibuang, bukan barisnya.** `In today's market, revenue grew 12%.` menjadi
   `Revenue grew 12%.` Menghapus barisnya adalah bug terburuk dalam riwayat proyek ini.
3. **Kerangka berhenti di batas tata bahasa.** Interjeksi (`Certainly!`) dan pembuka adverbial
   berhenti di tanda baca. Kata sambung (`note that`) tidak punya koma, jadi aturannya berhenti di
   kata `that` dan anak kalimatnya tetap.
4. **Pembuka multi-kata bersifat atomik.** `Sure thing!` adalah satu alternatif, karena mencocokkan
   `sure` saja dulu menghasilkan `Thing! Below is a walkthrough.`.
5. **Aturan pemisah tidak boleh memakan heading.** Garis bawah setext dideteksi dan dilindungi, dan
   verifier memakai pelindung yang sama, supaya heading yang sah tidak dilaporkan kotor.
6. **Awalan komentar dipatok ke posisi.** `#` hanya dianggap komentar di awal baris atau setelah
   spasi, dan itulah yang menjaga `x = "# end of loop"`.
7. **Urutan adalah kontrak:** karakter, kerangka, hapus baris, rapikan spasi.
8. **Akhir baris dan frontmatter dipertahankan byte per byte.**

## Struktur repositori

```text
antitextai/            paket: cleaner, scanner, verifier, CLI (tanpa dependensi)
tests/                 67 kasus unittest, bisa dijalankan dengan unittest atau pytest
SKILL.md               skill standar Agent Skills: aturan lengkap dan alur kerjanya
docs/                  integrasi agent, arsitektur, dan manual sidik jari AI
integrations/          file aturan siap salin untuk sepuluh tool
examples/              fixture kotor dan hasil bersihnya, byte per byte
scripts/               install.sh dan install.ps1
```

## Pengembangan

```bash
python -m unittest discover -s tests -t . -v          # seluruh suite, tanpa pytest
python -m antitextai verify CONTRIBUTING.md CHANGELOG.md integrations \
  antitextai/files.py antitextai/scan.py antitextai/verify.py antitextai/cli.py --strict
```

Perintah itu menyebut file satu per satu dengan sengaja. `SKILL.md`, README, manual di `docs/`,
`antitextai/cleaner.py`, dan `tests/` semuanya mengutip pola yang dicari alat ini sebagai data,
sama seperti linter yang menyimpan kode buruk di test suite-nya. Sisanya wajib lolos bersih, dan
`tests/test_selfcheck.py` menjaga hal itu.

Semuanya stdlib. Setiap asersi di `tests/` adalah cacat yang benar-benar terjadi saat pembuatan,
bukan contoh karangan. Lihat [`docs/architecture.md`](docs/architecture.md) untuk urutan aturan
dan mode kegagalan yang membentuk kode ini.

## Lisensi

MIT. Lihat [LICENSE](LICENSE).

Dibuat oleh [satriazoid](https://github.com/satriazoid), bersama Hermes Agent.

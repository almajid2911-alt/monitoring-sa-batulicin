# Dashboard Order Clone

Starter dashboard mirip contoh MORNING, dibuat pakai Flask + Bootstrap + DataTables + Chart.js.

## Jalankan lokal

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Buka:

```bash
http://127.0.0.1:5000
```

## Online dengan ngrok

Di terminal lain:

```bash
ngrok http 5000
```

Ambil URL `https://xxxx.ngrok-free.app` lalu buka dari mana saja.

## Next step

- Ganti data dummy di `app.py` dengan query database / API asli
- Tambah filter aktif di backend
- Tambah login jika mau dipakai publik

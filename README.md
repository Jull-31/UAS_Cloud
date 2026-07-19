# Item API — Proyek Akhir UAS Cloud Computing

Aplikasi multi-container: **REST API (Flask)** + **Database (PostgreSQL)**,
diorkestrasi dengan Docker Compose dan diuji otomatis lewat CI/CD (GitHub Actions).

## Arsitektur

```
Pengguna -> Aplikasi Web/REST API (Flask, container "app") -> Database (PostgreSQL, container "db")
```

- **app**: Flask REST API, port 8080 (host) -> 5000 (container)
- **db**: PostgreSQL 16, data disimpan di persistent volume `db_data`
- Kedua service terhubung lewat network internal `uas-network`
- `app` menunggu `db` benar-benar sehat (`depends_on: condition: service_healthy`) sebelum start

## Struktur Proyek

```
uas-cloud-computing/
|-- source-code/
|   |-- app.py
|   +-- requirements.txt
|-- tests/
|   |-- test_app.py
|   +-- requirements-test.txt
|-- Dockerfile
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- README.md
+-- .github/workflows/ci.yml
```

## Endpoint

| Method | Endpoint       | Deskripsi              |
|--------|----------------|--------------------------|
| GET    | `/health`      | Cek status app + koneksi database |
| GET    | `/items`       | Ambil semua item        |
| POST   | `/items`       | Tambah item baru (`{"name": ""}`) |
| GET    | `/items/<id>`  | Ambil item berdasarkan id |
| PUT    | `/items/<id>`  | Ubah item                |
| DELETE | `/items/<id>`  | Hapus item                |

## Menjalankan dengan Docker Compose (cara utama)

1. Salin file environment:
   ```
   copy .env.example .env
   ```
   (di Mac/Linux: `cp .env.example .env`)

2. Jalankan:
   ```
   docker compose up -d
   docker compose ps
   ```

3. Cek aplikasi:
   ```
   http://localhost:8080/health
   ```

4. Matikan:
   ```
   docker compose down
   ```

   Data database tetap tersimpan di volume `db_data` walau container dimatikan.
   Untuk menghapus data sepenuhnya: `docker compose down -v`

## Simulasi Ketahanan Layanan

```
docker compose stop app
docker compose start app
docker compose ps
```
Setelah `app` restart, `/health` akan kembali `healthy` dan data di database tetap ada
karena tersimpan di persistent volume, bukan di dalam container.

## Menjalankan Automated Test

```
docker compose up -d db
pip install -r tests/requirements-test.txt
pytest tests/ -v
```
(pastikan environment variable `DATABASE_URL` mengarah ke `localhost:5432`)

## CI/CD (GitHub Actions)

Setiap push/PR ke branch `main` akan otomatis:
1. Menyalakan service container PostgreSQL
2. Install dependency
3. Menjalankan automated test (6 test: health check, validasi input, CRUD, error handling)
4. Build Docker image aplikasi

Lihat `.github/workflows/ci.yml`.

## Catatan Keamanan

- File `.env` tidak ikut ter-commit ke repository (lihat `.gitignore`).
- Kredensial database dikelola lewat environment variable, bukan hardcode di kode.

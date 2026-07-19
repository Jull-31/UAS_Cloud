"""
Item API - Proyek Akhir UAS Cloud Computing
Implementasi Aplikasi Multi-Container dengan Docker, Orkestrasi, dan CI/CD

Arsitektur: 2 service -> app (Flask/Python) + db (PostgreSQL)

Endpoint:
    GET  /health            -> cek status aplikasi & koneksi database
    GET  /items              -> ambil semua item
    POST /items               -> tambah item baru
    GET  /items/<item_id>     -> ambil satu item berdasarkan id
    PUT  /items/<item_id>     -> ubah item
    DELETE /items/<item_id>   -> hapus item
"""

import os
import time
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/itemdb",
)


def get_connection():
    """Buat koneksi baru ke database PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)


def init_db(retries=10, delay=2):
    """
    Inisialisasi tabel items.
    Diberi retry karena saat docker compose up, container app bisa
    mencoba connect sebelum database benar-benar siap menerima koneksi.
    """
    last_error = None
    for _ in range(retries):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                );
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except psycopg2.OperationalError as e:
            last_error = e
            time.sleep(delay)
    raise RuntimeError(f"Gagal konek ke database setelah beberapa percobaan: {last_error}")


@app.get("/health")
def health():
    """Health check: memastikan aplikasi hidup DAN database bisa diakses."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 503


@app.get("/items")
def get_items():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name FROM items ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@app.post("/items")
def create_item():
    data = request.get_json(silent=True)
    if not data or "name" not in data or not str(data["name"]).strip():
        return jsonify({"error": "Field 'name' wajib diisi"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name) VALUES (%s) RETURNING id;", (data["name"],))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "name": data["name"]}), 201


@app.get("/items/<int:item_id>")
def get_item(item_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name FROM items WHERE id = %s;", (item_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return jsonify({"error": "Item tidak ditemukan"}), 404
    return jsonify(row), 200


@app.put("/items/<int:item_id>")
def update_item(item_id):
    data = request.get_json(silent=True)
    if not data or "name" not in data or not str(data["name"]).strip():
        return jsonify({"error": "Field 'name' wajib diisi"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE items SET name = %s WHERE id = %s;", (data["name"], item_id))
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        return jsonify({"error": "Item tidak ditemukan"}), 404
    return jsonify({"id": item_id, "name": data["name"]}), 200


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = %s;", (item_id,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Item tidak ditemukan"}), 404
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

"""Local control API for the Myohan video-generation workflow.

This first milestone stores and monitors generation briefs only. It does not
load a model or claim to render video; model workers will be added separately.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from manifest import build_manifest
from models import model_for_preset

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
DB_PATH = RUNTIME / "video_jobs.sqlite3"
HOST = "127.0.0.1"
PORT = 8765
MAX_BODY = 64 * 1024
PRESETS = {"local_preview", "standard_scene", "premium_scene"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect_db() -> sqlite3.Connection:
    RUNTIME.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        title TEXT NOT NULL,
        pillar TEXT NOT NULL,
        space TEXT NOT NULL,
        bed TEXT NOT NULL,
        minutes REAL NOT NULL,
        preset TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        payload TEXT NOT NULL
    )""")
    conn.commit()
    return conn


def public_job(row: sqlite3.Row) -> dict:
    payload = json.loads(row["payload"])
    return {
        "id": row["id"], "itemId": row["item_id"], "title": row["title"],
        "pillar": row["pillar"], "space": row["space"], "bed": row["bed"],
        "minutes": row["minutes"], "kind": payload.get("kind", "long"),
        "preset": row["preset"], "status": row["status"],
        "modelId": model_for_preset(row["preset"])["modelId"],
        "createdAt": row["created_at"],
        "manifestUrl": f"/api/v1/jobs/{row['id']}/manifest",
        "message": "모델 검증 대상으로 매칭됨 · 추론/영상 생성은 아직 실행되지 않았습니다.",
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, status: int, value: dict | list):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/v1/health":
            self.send_json(200, self.health())
            return
        if path == "/api/v1/jobs":
            with connect_db() as conn:
                rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50").fetchall()
            self.send_json(200, [public_job(row) for row in rows])
            return
        if path.startswith("/api/v1/jobs/") and path.endswith("/manifest"):
            job_id = path.removeprefix("/api/v1/jobs/").removesuffix("/manifest").strip("/")
            with connect_db() as conn:
                row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                self.send_json(404, {"error": "작업을 찾을 수 없습니다."})
            else:
                self.send_json(200, build_manifest(row["id"], json.loads(row["payload"]), row["created_at"]))
            return
        if path.startswith("/api/"):
            self.send_json(404, {"error": "not_found"})
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/v1/jobs":
                self.create_job()
                return
            if path.startswith("/api/v1/jobs/") and path.endswith("/cancel"):
                job_id = path.removeprefix("/api/v1/jobs/").removesuffix("/cancel").strip("/")
                self.cancel_job(job_id)
                return
            self.send_json(404, {"error": "not_found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("요청 크기가 비어 있거나 허용 한도를 초과했습니다.")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("요청 본문은 JSON 객체여야 합니다.")
        return value

    def create_job(self):
        data = self.read_json()
        required = ("itemId", "title", "pillar", "space", "bed", "minutes", "preset")
        if any(key not in data for key in required):
            raise ValueError("필수 항목이 누락되었습니다.")
        preset = str(data["preset"])
        if preset not in PRESETS:
            raise ValueError("지원하지 않는 GPU 프리셋입니다.")
        try:
            minutes = float(data["minutes"])
        except (TypeError, ValueError):
            raise ValueError("영상 길이는 숫자여야 합니다.")
        if not 0 < minutes <= 180:
            raise ValueError("영상 길이는 0분 초과, 180분 이하여야 합니다.")
        fields = {key: str(data[key]).strip() for key in ("itemId", "title", "pillar", "space", "bed")}
        if any(not value or len(value) > 300 for value in fields.values()):
            raise ValueError("문자 항목은 비어 있을 수 없고 300자를 넘을 수 없습니다.")
        job_id = str(uuid.uuid4())
        created_at = now_iso()
        kind = str(data.get("kind", "shorts" if minutes <= 1 else "long"))
        if kind not in {"shorts", "long"}:
            raise ValueError("영상 형식은 shorts 또는 long이어야 합니다.")
        payload = {**fields, "minutes": minutes, "preset": preset, "kind": kind}
        with connect_db() as conn:
            conn.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (job_id, fields["itemId"], fields["title"], fields["pillar"],
                 fields["space"], fields["bed"], minutes, preset, "draft",
                 created_at, json.dumps(payload, ensure_ascii=False)),
            )
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        self.send_json(201, public_job(row))

    def cancel_job(self, job_id: str):
        with connect_db() as conn:
            cur = conn.execute("UPDATE jobs SET status = 'cancelled' WHERE id = ? AND status = 'draft'", (job_id,))
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            self.send_json(404, {"error": "작업을 찾을 수 없습니다."})
        elif cur.rowcount == 0:
            self.send_json(409, {"error": "현재 상태에서는 취소할 수 없습니다."})
        else:
            self.send_json(200, public_job(row))

    @staticmethod
    def health() -> dict:
        gpu = None
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=2, check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu = result.stdout.strip().splitlines()
        except (OSError, subprocess.TimeoutExpired):
            pass
        return {
            "service": "myohan-local-controller",
            "api": "ok",
            "inferenceReady": False,
            "workerReady": False,
            "gpuDetected": gpu or [],
            "message": "컨트롤러 연결됨 · 프롬프트 명세 생성 가능 · 영상 모델 워커 미연결",
        }


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"묘한 명상 로컬 컨트롤러: http://{HOST}:{PORT}")
    print("안전상 로컬 PC에서만 접속할 수 있습니다. 종료하려면 터미널에서 Ctrl+C를 누르세요.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("서버를 종료합니다.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

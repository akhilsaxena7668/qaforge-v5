"""QAForge Gemini — FastAPI Backend v4.0"""

import os, json, uuid, base64
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load backend/.env
def _load_env():
    p = Path(__file__).parent / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() and v.strip() and k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()
_load_env()

from .ai_engine import AIEngine, MODEL_LABELS, MODEL_CHAIN
from .test_executor import TestExecutor
from .report_gen import ReportGenerator
from .models import GenerateRequest, ExecuteRequest, BugScanRequest, AppConfig, RangeConfig
from .antivirus import AntivirusScanner

app = FastAPI(title="QAForge Gemini API", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def _env(n):
    return os.environ.get(f"GEMINI_API_KEY_{n}", "")

from typing import Any

store: dict[str, Any] = {
    "suites":  {},
    "results": {},
    "scans":   {},
    "config": {
        "api_key_1":     _env(1),
        "api_key_2":     _env(2),
        "api_key_3":     _env(3),
        "api_key_4":     _env(4),
        "default_model": os.environ.get("DEFAULT_MODEL", "pro"),
    }
}

ai       = AIEngine(store)
executor = TestExecutor()
reporter = ReportGenerator()

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
QUARANTINE_DIR = Path("reports/quarantine")
QUARANTINE_DIR.mkdir(exist_ok=True, parents=True)

av_scanner = AntivirusScanner(ai)

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    keys = ai._get_keys()
    return {
        "status": "ok",
        "version": "4.0.0",
        "api_connected": bool(keys),
        "keys_configured": len(keys),
        "model_status": ai.get_model_status(),
        "timestamp": datetime.now().isoformat(),
    }

# ── Config ─────────────────────────────────────────────────────────────────────
@app.get("/api/config")
async def get_config():
    cfg = dict(store["config"])
    for i in range(1, 5):
        k = str(cfg.get(f"api_key_{i}", ""))
        cfg[f"api_key_{i}"] = (k[:6] + "••••" + k[-3:]) if len(k) > 9 else ("••••••" if k else "")  # type: ignore
    cfg["keys_configured"] = len(ai._get_keys())
    cfg["model_status"] = ai.get_model_status()
    return cfg

@app.post("/api/config")
async def save_config(config: AppConfig):
    for i in range(1, 5):
        val = getattr(config, f"api_key_{i}", None)
        if val and "••" not in val:
            store["config"][f"api_key_{i}"] = val.strip()
    if config.default_model:
        store["config"]["default_model"] = config.default_model
    ai.reset_quota()
    keys = ai._get_keys()
    return {"status": "saved", "keys_configured": len(keys), "api_connected": bool(keys), "model_status": ai.get_model_status()}

@app.post("/api/quota/reset")
async def reset_quota():
    ai.reset_quota()
    return {"status": "reset", "model_status": ai.get_model_status()}

# ── Generate ───────────────────────────────────────────────────────────────────
@app.post("/api/generate/url")
async def gen_url(req: GenerateRequest):
    suite = await ai.generate_from_url(req)
    store["suites"][suite.id] = suite.dict()
    return suite

@app.post("/api/generate/text")
async def gen_text(req: GenerateRequest):
    suite = await ai.generate_from_text(req)
    store["suites"][suite.id] = suite.dict()
    return suite

@app.post("/api/generate/image")
async def gen_image(
    file: UploadFile = File(...),
    app_type: str = Form("web"),
    description: str = Form(""),
    focus_areas: str = Form(""),
    critical_count: int = Form(0),
    high_count: int = Form(0),
    min_tests: int = Form(10),
    max_tests: int = Form(20),
    is_multi_agent: bool = Form(False),
    agents: str = Form(""),
    depth: str = Form("standard"),
):
    data = await file.read()
    b64  = base64.b64encode(data).decode()
    rc   = RangeConfig(min_tests=min_tests, max_tests=max_tests)
    fa_list = [f.strip() for f in focus_areas.split(",") if f.strip()]
    agent_list = [a.strip() for a in agents.split(",") if a.strip()]
    suite = await ai.generate_from_image(b64, file.content_type or "image/png", app_type, description, fa_list, rc, is_multi_agent, agent_list, depth=depth)
    store["suites"][suite.id] = suite.dict()
    return suite

@app.post("/api/generate/video")
async def gen_video(
    file: UploadFile = File(...),
    app_type: str = Form("web"),
    description: str = Form(""),
    focus_areas: str = Form(""),
    critical_count: int = Form(0),
    high_count: int = Form(0),
    min_tests: int = Form(10),
    max_tests: int = Form(20),
    is_multi_agent: bool = Form(False),
    agents: str = Form(""),
    depth: str = Form("standard"),
):
    data = await file.read()
    b64  = base64.b64encode(data).decode()
    rc   = RangeConfig(min_tests=min_tests, max_tests=max_tests)
    fa_list = [f.strip() for f in focus_areas.split(",") if f.strip()]
    agent_list = [a.strip() for a in agents.split(",") if a.strip()]
    suite = await ai.generate_from_video(b64, file.content_type or "video/mp4", app_type, description, fa_list, rc, is_multi_agent, agent_list, depth=depth)
    store["suites"][suite.id] = suite.dict()
    return suite

# ── Bug Scan ───────────────────────────────────────────────────────────────────
@app.post("/api/scan/bugs")
async def bug_scan(req: BugScanRequest):
    result = await ai.bug_scan(req.app_type, req.description or "", req.url, getattr(req, "depth", "standard"), getattr(req, "categories", []))
    store["scans"][result["scan_id"]] = result
    return result

@app.get("/api/scans")
async def list_scans():
    return list(store["scans"].values())

@app.get("/api/scans/{sid}")
async def get_scan(sid: str):
    return _404(store["scans"], sid, "Scan")

@app.get("/api/scans/{sid}/download")
async def dl_scan(sid: str):
    scan = _404(store["scans"], sid, "Scan")
    p = REPORTS_DIR / f"scan_{str(sid)[:8]}.json"  # type: ignore
    p.write_text(json.dumps(scan, indent=2))
    return FileResponse(p, media_type="application/json", filename=p.name)

# ── Suites ─────────────────────────────────────────────────────────────────────
@app.get("/api/suites")
async def list_suites():
    return list(store["suites"].values())

@app.get("/api/suites/{sid}")
async def get_suite(sid: str):
    return _404(store["suites"], sid, "Suite")

@app.delete("/api/suites/{sid}")
async def del_suite(sid: str):
    store["suites"].pop(sid, None)
    return {"deleted": sid}

@app.get("/api/suites/{sid}/download")
async def dl_suite(sid: str):
    suite = _404(store["suites"], sid, "Suite")
    p = REPORTS_DIR / f"suite_{str(sid)[:8]}.json"  # type: ignore
    p.write_text(json.dumps(suite, indent=2))
    return FileResponse(p, media_type="application/json", filename=p.name)

# ── Execute ────────────────────────────────────────────────────────────────────
@app.post("/api/execute/{sid}")
async def execute(sid: str, req: ExecuteRequest, bg: BackgroundTasks):
    suite = _404(store["suites"], sid, "Suite")
    run_id = str(uuid.uuid4())
    store["results"][run_id] = {
        "run_id": run_id, "suite_id": sid, "suite_name": suite["name"],
        "environment": req.environment, "status": "running", "progress": 0,
        "started_at": datetime.now().isoformat(), "tests": [],
    }
    bg.add_task(_run, run_id, sid, req)
    return {"run_id": run_id, "status": "running"}

async def _run(run_id: str, sid: str, req: ExecuteRequest):
    suite = store["suites"][sid]
    tests = suite["tests"]
    results: list[dict[str, Any]] = []
    sem = asyncio.Semaphore(15) # Run 15 simulations in parallel

    async def run_with_progress(t):
        async with sem:
            res = await executor.run_test(t, req.environment, req.base_url)
            results.append(res)
            # Update combined state for the frontend poller
            store["results"][run_id]["tests"] = list(results)
            store["results"][run_id]["progress"] = round(len(results) / len(tests) * 100)
            return res

    await asyncio.gather(*(run_with_progress(t) for t in tests))
    passed = sum(1 for r in results if r["status"] == "pass")
    store["results"][run_id].update({
        "status": "completed", "completed_at": datetime.now().isoformat(),
        "summary": {
            "total": len(results), "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": round(float(passed)/len(results)*100, 1) if results else 0.0,  # type: ignore
        }
    })

@app.get("/api/results")
async def list_results():
    return list(store["results"].values())

@app.get("/api/results/{run_id}")
async def get_result(run_id: str):
    return _404(store["results"], run_id, "Run")

# ── Reports ────────────────────────────────────────────────────────────────────
@app.post("/api/reports/{run_id}")
async def make_report(run_id: str, fmt: str = "html"):
    result = _404(store["results"], run_id, "Run")
    suite  = store["suites"].get(result["suite_id"], {})
    path   = reporter.generate(result, suite, fmt, REPORTS_DIR)
    return {"filename": path.name}

@app.get("/api/reports/download/{filename}")
async def dl_report(filename: str):
    path = REPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Report not found")
    mmap = {".html":"text/html",".json":"application/json",
            ".xlsx":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    return FileResponse(path, media_type=mmap.get(path.suffix,"application/octet-stream"), filename=filename)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _404(d, key, label):
    if key not in d:
        raise HTTPException(404, f"{label} not found")
    return d[key]

# ── ANTIVIRUS SCAN ───────────────────────────────────────────────────────────
from pydantic import BaseModel
class DeleteRequest(BaseModel):
    filepath: str

@app.post("/api/scan/antivirus")
async def scan_antivirus(file: UploadFile = File(...)):
    content = await file.read()
    text_content = content.decode("utf-8", errors="ignore")
    
    # Save to quarantine
    safe_name = f"{str(uuid.uuid4().hex)[:8]}_{file.filename}"  # type: ignore
    q_path = QUARANTINE_DIR / safe_name
    q_path.write_bytes(content)
    
    report = await av_scanner.scan_hybrid(text_content, file.filename)
    report["quarantine_path"] = str(q_path)
    return report

@app.delete("/api/scan/antivirus/delete")
async def delete_antivirus_file(req: DeleteRequest):
    try:
        p = Path(req.filepath)
        if p.exists() and "quarantine" in p.parts:
            p.unlink()
            return {"status": "deleted"}
        raise HTTPException(404, "File not found or not in quarantine")
    except Exception as e:
        raise HTTPException(500, str(e))

class DirectoryScanRequest(BaseModel):
    path: str

@app.post("/api/scan/directory")
async def scan_directory_endpoint(req: DirectoryScanRequest):
    try:
        results = await av_scanner.scan_directory(req.path)
        return {"status": "success", "threats": results}
    except Exception as e:
        raise HTTPException(500, f"Failed to scan directory: {e}")

@app.delete("/api/scan/directory/delete")
async def delete_deep_threat(req: DeleteRequest):
    try:
        p = Path(req.filepath)
        if p.exists() and p.is_file():
            p.unlink()
            return {"status": "deleted"}
        raise HTTPException(404, "File not found")
    except Exception as e:
        raise HTTPException(500, str(e))

# ── BLOGS ──────────────────────────────────────────────────────────────────────
BLOG_CACHE_FILE = Path(__file__).parent.parent / "reports" / "daily_blogs.json"

@app.get("/api/blogs")
async def get_daily_blogs():
    print(f"[QAForge] Blog request received. Cache: {BLOG_CACHE_FILE}")
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if BLOG_CACHE_FILE.exists():
            cache = json.loads(BLOG_CACHE_FILE.read_text())
            if cache.get("date") == today:
                print(f"[QAForge] Returning cached blogs (count: {len(cache.get('blogs', []))})")
                return cache.get("blogs", [])
    except Exception as e:
        print(f"[QAForge] Cache read failed: {e}")

    print("[QAForge] Cache empty or stale. Generating new blogs...")
    blogs = await ai.generate_daily_blogs()
    print(f"[QAForge] AI returned {len(blogs)} blogs")
    
    if blogs:
        try:
            BLOG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            BLOG_CACHE_FILE.write_text(json.dumps({"date": today, "blogs": blogs}, indent=2))
            print(f"[QAForge] Saved {len(blogs)} blogs to cache")
        except Exception as e:
            print(f"[QAForge] Cache write failed: {e}")
    else:
        print("[QAForge] No blogs generated to save")
    return blogs


@app.get("/api/blogs/{blog_id}")
async def get_blog_detail(blog_id: str):
    print(f"[QAForge] Detail request for: {blog_id}")
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if BLOG_CACHE_FILE.exists():
            cache = json.loads(BLOG_CACHE_FILE.read_text())
            if cache.get("date") == today:
                blogs = cache.get("blogs", [])
                for b in blogs:
                    if b.get("id") == blog_id:
                        return b
    except Exception as e:
        print(f"[QAForge] Detail fetch failed: {e}")
    
    # If not in cache, try to regenerate (or return 404)
    raise HTTPException(status_code=404, detail="Blog post not found")

# ── Frontend ───────────────────────────────────────────────────────────────────
_fe = Path(__file__).parent.parent / "frontend"
if _fe.exists():
    app.mount("/", StaticFiles(directory=str(_fe), html=True), name="frontend")

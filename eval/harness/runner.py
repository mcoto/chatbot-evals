# eval/harness/runner.py
from __future__ import annotations
import argparse, os, time, json, datetime as dt
from pathlib import Path
import yaml, requests
from sqlalchemy import create_engine, text
from comparators import (
    equals, approx_equals, not_null, regex, contains, eval_condition, get_from
)
from kpis import compute_kpis

DEFAULTS = {
    "CHATBOT_URL": os.environ.get("CHATBOT_URL", "http://localhost:8000"),
    "DB_URL": os.environ.get("DB_URL", "postgresql+psycopg://gtuser:gtpass@localhost:5432/groundtruth"),
}

def run_sql(db_url: str, query: str, args: dict) -> dict:
    eng = create_engine(db_url, pool_pre_ping=True)
    with eng.connect() as conn:
        row = conn.execute(text(query), args).mappings().first()
        return dict(row) if row else {}
    
def run_http(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    method = method.upper()
    if method == "GET":
        r = requests.get(url, timeout=10)
    else:
        r = requests.post(url, json=payload or {}, timeout=15)
    r.raise_for_status()
    return r.json()

def call_chatbot(chatbot_url: str, body: dict) -> dict:
    r = requests.post(f"{chatbot_url}/chat", json=body, timeout=20)
    r.raise_for_status()
    data = r.json()
    return {"text": data.get("response"), "json": data}

def eval_check(check: dict, truth: dict, response: dict) -> dict:
    ctype = check["type"]
    passed = False
    info = {}

    # Helpers to fetch values from dotted paths
    def _get_from_response(path: str):
        # supports response.text and response.json.*
        if path.startswith("response.text"):
            return response.get("text")
        elif path.startswith("response.json."):
            return get_from(response.get("json", {}), path[len("response.json."):])
        return None

    if ctype == "equals":
        left = _get_from_response(check["left"])
        right = get_from(truth, check["right"])
        passed = equals(left, right)
        info = {"left": left, "right": right}

    elif ctype == "approx_equals":
        left = _get_from_response(check["left"])
        right = get_from(truth, check["right"])
        tol = float(check.get("tolerance", 0.0))
        passed = approx_equals(left, right, tol)
        info = {"left": left, "right": right, "tolerance": tol}

    elif ctype == "not_null":
        val = _get_from_response(check["from"])
        passed = not_null(val)
        info = {"value": val}

    elif ctype == "regex":
        val = _get_from_response(check["from"])
        pat = check["pattern"]
        passed = regex(val, pat)
        info = {"value": val, "pattern": pat}

    elif ctype == "contains":
        hay = _get_from_response(check["haystack"])
        needle = check["needle"]
        passed = contains(hay, needle)
        info = {"haystack": hay, "needle": needle}

    elif ctype in ("required_if", "contains_if"):
        cond = check["condition"]
        cond_ok = eval_condition(truth, response, cond)
        if ctype == "required_if":
            # Si la condición aplica, 'contains' debe ser True
            hay = _get_from_response(check["from"])
            needle = check["contains"]
            passed = (not cond_ok) or contains(hay, needle)
            info = {"condition": cond, "applies": cond_ok, "haystack": hay, "needle": needle}
        else:
            hay = _get_from_response(check["haystack"])
            needle = check["needle"]
            passed = (not cond_ok) or contains(hay, needle)
            info = {"condition": cond, "applies": cond_ok, "haystack": hay, "needle": needle}

    else:
        raise ValueError(f"Unknown check type: {ctype}")

    return {"type": ctype, "name": check.get("name", ctype), "passed": passed, "info": info}

def ensure_outdir() -> Path:
    out = Path("eval/reports") / dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=True)
    return out

def write_report_md(outdir: Path, spec_id: str, results: dict, kpis) -> Path:
    md = []
    md.append(f"# Evaluation Report — {spec_id}")
    md.append("")
    md.append(f"- Timestamp (UTC): {dt.datetime.utcnow().isoformat()}Z")
    md.append(f"- Risk weight: {results['risk_weight']}")
    md.append("")
    md.append("## Checks")
    for r in results["checks"]:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        md.append(f"- **{r['name']}** (`{r['type']}`): {status}")
        if r.get("info"):
            md.append(f"  - info: `{json.dumps(r['info'], ensure_ascii=False)}`")
    md.append("")
    md.append("## KPIs")
    md.append(f"- Total checks: **{kpis.total_checks}**")
    md.append(f"- Passed checks: **{kpis.passed_checks}**")
    md.append(f"- Factual failures: **{kpis.factual_failures}**")
    md.append(f"- Compliance failures: **{kpis.compliance_failures}**")
    md.append(f"- RFI (risk-weighted factuality): **{kpis.rfi:.3f}**")
    md.append(f"- EDR (escalation deflection): **{kpis.edr:.3f}**")
    md.append(f"- NCS (net compliance score): **{kpis.ncs:.3f}**")
    outpath = outdir / f"{spec_id}.md"
    outpath.write_text("\n".join(md), encoding="utf-8")
    return outpath

def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    ap = argparse.ArgumentParser(description="Chatbot Eval Harness (live truth)")
    ap.add_argument("--spec", required=True, help="Path to spec YAML")
    ap.add_argument("--chatbot-url", default=DEFAULTS["CHATBOT_URL"])
    ap.add_argument("--db-url", default=DEFAULTS["DB_URL"])
    args = ap.parse_args()

    spec = load_spec(args.spec)
    risk_weight = float(spec.get("risk_weight", 1.0))

    # 1) Obtener verdad viva (truth_ops)
    truth = {}
    for op in spec.get("truth_ops", []):
        if op["type"] == "sql":
            res = run_sql(args.db_url, op["query"], op.get("args", {}))
            truth[op["id"]] = res
        elif op["type"] == "http":
            res = run_http(op["url"], op.get("method", "GET"), op.get("payload"))
            truth[op["id"]] = res
        else:
            raise ValueError(f"Unknown truth op type: {op['type']}")

    # 2) Invocar chatbot
    body = spec["invoke"]["body"]
    if "chatbot_url" in spec["invoke"]:
        chatbot_url = spec["invoke"]["chatbot_url"]
    else:
        chatbot_url = args.chatbot_url

    response = call_chatbot(chatbot_url, body)

    # 3) Checks
    check_results = []
    for chk in spec.get("checks", []):
        res = eval_check(chk, truth, response)
        check_results.append(res)

    # 4) KPIs y reporte
    kpis = compute_kpis(check_results, risk_weight=risk_weight)
    outdir = ensure_outdir()
    report_path = write_report_md(outdir, spec.get("id", Path(args.spec).stem),
                                  {"checks": check_results, "risk_weight": risk_weight}, kpis)

    print(f"[OK] Report written: {report_path}")

if __name__ == "__main__":
    main()


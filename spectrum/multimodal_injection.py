import os
import re
import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH = True
except ImportError:
    RICH = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

console = Console() if RICH else None

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "multimodal_reports"
REPORT_DIR.mkdir(exist_ok=True)

# ── Injection patterns (same as LobsterTrap in demo_server.py) ──────────────

INJECTION_PATTERNS = [
    (r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)", "CRITICAL", "Instruction override attempt"),
    (r"forget\s+(your|all)\s+(instructions?|rules?|training)", "CRITICAL", "Memory wipe attempt"),
    (r"you\s+are\s+now\s+a?\s*\w+", "HIGH", "Role hijack attempt"),
    (r"pretend\s+(you\s+are|to\s+be)", "HIGH", "Persona injection"),
    (r"act\s+as\s+(if\s+you\s+(are|were))?\s*\w+", "HIGH", "Act-as injection"),
    (r"(jailbreak|dan\s+mode|developer\s+mode|god\s+mode)", "CRITICAL", "Jailbreak keyword"),
    (r"(bypass|override|disable)\s+(safety|filter|guardrail|policy|restriction)", "CRITICAL", "Safety bypass attempt"),
    (r"reveal\s+(the\s+)?(system\s+prompt|instructions?|secrets?|password|key)", "HIGH", "Secret extraction attempt"),
    (r"print\s+(your\s+)?(system\s+prompt|instructions?|context)", "HIGH", "Prompt extraction attempt"),
    (r"what\s+(are|is)\s+your\s+(instructions?|system\s+prompt|rules?)", "MEDIUM", "Prompt probing"),
    (r"\{\{.*?\}\}", "HIGH", "Template injection (SSTI)"),
    (r"<script[\s>]", "HIGH", "Script injection (XSS)"),
    (r"'[\s]*;[\s]*--", "MEDIUM", "SQL injection pattern"),
    (r"(sudo|chmod|rm\s+-rf|curl\s+http|wget\s+http)", "HIGH", "Command injection attempt"),
    (r"(system\s+prompt|initial\s+prompt)\s*[:=]", "HIGH", "Prompt definition override"),
    (r"(translate|repeat|echo|output)\s+(this|the\s+following)\s+(in\s+full|exactly|verbatim)", "MEDIUM", "Extraction via translation"),
    (r"new\s+(goal|objective|task|mission)\s*[:=]", "HIGH", "Goal hijack"),
    (r"from\s+now\s+on\s+(you|your|act)", "HIGH", "Persistent instruction injection"),
    (r"(hidden|secret|invisible)\s+(instruction|command|message)", "CRITICAL", "Hidden instruction marker"),
    (r"<!-- .* -->|/\*.*\*/", "MEDIUM", "Comment-style hidden instruction"),
]

SUSPICIOUS_PATTERNS = [
    (r"admin|root|superuser", "LOW", "Privilege keyword"),
    (r"password|credential|token|api.?key|secret", "LOW", "Credential keyword"),
    (r"delete|drop|truncate|destroy", "LOW", "Destructive keyword"),
    (r"exfiltrate|leak|send\s+to|upload\s+to", "MEDIUM", "Data exfiltration keyword"),
]


# ── Image text extraction ────────────────────────────────────────────────────

def extract_text_from_image_gemini(image_path: str, api_key: str) -> dict:
    """
    Use Gemini vision to extract ALL text from an image,
    including text that may be hidden, small, or watermarked.
    """
    if not GEMINI_AVAILABLE:
        return {"success": False, "error": "google-genai not installed", "text": ""}

    try:
        client = genai.Client(api_key=api_key)
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = Path(image_path).suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".gif": "image/gif",
                    ".webp": "image/webp", ".bmp": "image/bmp"}
        mime_type = mime_map.get(ext, "image/png")

        prompt = (
            "Extract ALL text visible in this image. "
            "Include: normal text, watermarks, small text, text in corners, "
            "text with low opacity, text in any language, text overlaid on images. "
            "Do NOT summarize or interpret — just extract the raw text exactly as it appears. "
            "If no text is found, say: NO_TEXT_FOUND"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part(
                            inline_data=genai_types.Blob(
                                mime_type=mime_type,
                                data=image_bytes
                            )
                        ),
                        genai_types.Part(text=prompt),
                    ]
                )
            ]
        )
        extracted = response.text.strip()
        return {
            "success": True,
            "method": "gemini-vision",
            "text": extracted if extracted != "NO_TEXT_FOUND" else "",
            "raw_response": extracted,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "text": ""}


def extract_text_from_image_ocr(image_path: str) -> dict:
    """
    Fallback OCR using pytesseract (works offline, no API needed).
    """
    if not OCR_AVAILABLE:
        return {"success": False, "error": "pytesseract / Pillow not installed", "text": ""}

    try:
        img = Image.open(image_path)
        # Try multiple OCR configs for better coverage
        configs = [
            "--psm 3",   # Fully automatic page segmentation
            "--psm 6",   # Uniform block of text
            "--psm 11",  # Sparse text (good for watermarks)
        ]
        all_text = set()
        for cfg in configs:
            try:
                text = pytesseract.image_to_string(img, config=cfg).strip()
                if text:
                    all_text.add(text)
            except Exception:
                pass

        combined = "\n".join(all_text)
        return {
            "success": True,
            "method": "pytesseract-ocr",
            "text": combined,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "text": ""}


def extract_text_from_image(image_path: str, gemini_api_key: str = None) -> dict:
    """
    Extract text from image — tries Gemini first, falls back to OCR.
    """
    if gemini_api_key and GEMINI_AVAILABLE:
        result = extract_text_from_image_gemini(image_path, gemini_api_key)
        if result["success"]:
            return result

    if OCR_AVAILABLE:
        return extract_text_from_image_ocr(image_path)

    return {
        "success": False,
        "error": "No extraction method available. Install google-genai or pytesseract+Pillow.",
        "text": "",
    }


# ── Injection analysis ───────────────────────────────────────────────────────

def analyse_text_for_injection(text: str) -> dict:
    """
    Scan extracted text for prompt injection patterns.
    Returns structured findings.
    """
    if not text or not text.strip():
        return {
            "injection_detected": False,
            "risk_level": "NONE",
            "risk_score": 0.0,
            "findings": [],
            "suspicious": [],
        }

    text_lower = text.lower()
    findings = []
    suspicious_hits = []

    for pattern, severity, label in INJECTION_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
        if matches:
            findings.append({
                "pattern": pattern,
                "severity": severity,
                "label": label,
                "match_count": len(matches),
                "sample": str(matches[0])[:80],
            })

    for pattern, severity, label in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            suspicious_hits.append({
                "pattern": pattern,
                "severity": severity,
                "label": label,
                "match_count": len(matches),
            })

    # Risk scoring
    severity_weights = {"CRITICAL": 1.0, "HIGH": 0.7, "MEDIUM": 0.4, "LOW": 0.15}
    raw_score = sum(severity_weights.get(f["severity"], 0) for f in findings)
    raw_score += sum(severity_weights.get(s["severity"], 0) * 0.3 for s in suspicious_hits)
    risk_score = min(round(raw_score, 3), 1.0)

    if risk_score >= 0.7 or any(f["severity"] == "CRITICAL" for f in findings):
        risk_level = "CRITICAL"
    elif risk_score >= 0.4 or any(f["severity"] == "HIGH" for f in findings):
        risk_level = "HIGH"
    elif risk_score > 0.1:
        risk_level = "MEDIUM"
    elif suspicious_hits:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    return {
        "injection_detected": len(findings) > 0,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "findings": findings,
        "suspicious": suspicious_hits,
    }


# ── Main scanner ─────────────────────────────────────────────────────────────

def scan_image(
    image_path: str,
    gemini_api_key: str = None,
    api_key: str = None,       # Spectrum enterprise API key for audit logging
    log_to_audit: bool = True,
) -> dict:
    """
    Full multimodal injection scan on a single image.

    Returns a complete scan report dict.
    """
    image_path = str(image_path)
    if not Path(image_path).exists():
        return {"error": f"File not found: {image_path}"}

    file_name = Path(image_path).name
    file_hash = _hash_file(image_path)
    timestamp = datetime.now().isoformat()

    if console:
        console.print(f"\n[bold cyan]🔍 Scanning image: {file_name}[/bold cyan]")

    # Step 1: Extract text
    extraction = extract_text_from_image(image_path, gemini_api_key)
    extracted_text = extraction.get("text", "")

    if console:
        method = extraction.get("method", "none")
        if extraction["success"]:
            console.print(f"[dim]Extraction method: {method}[/dim]")
            if extracted_text:
                console.print(Panel(extracted_text[:500], title="Extracted Text", border_style="blue"))
            else:
                console.print("[dim]No text found in image.[/dim]")
        else:
            console.print(f"[yellow]Extraction failed: {extraction.get('error')}[/yellow]")

    # Step 2: Analyse for injection
    analysis = analyse_text_for_injection(extracted_text)

    # Step 3: Build report
    report = {
        "scan_id": f"SCAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{file_hash[:8]}",
        "timestamp": timestamp,
        "file": file_name,
        "file_hash_sha256": file_hash,
        "extraction": {
            "method": extraction.get("method", "failed"),
            "success": extraction.get("success", False),
            "text_length": len(extracted_text),
            "extracted_text": extracted_text[:2000],  # cap for report
        },
        "analysis": analysis,
        "verdict": _verdict(analysis),
    }

    # Step 4: Print result
    if console:
        _print_scan_result(report)

    # Step 5: Save report
    report_path = REPORT_DIR / f"{report['scan_id']}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Step 6: Audit log
    if log_to_audit and api_key:
        try:
            import importlib.util
            _audit_path = BASE_DIR / "audit.py"
            _spec = importlib.util.spec_from_file_location("audit", _audit_path)
            audit_mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(audit_mod)
            audit_mod.log_action(
                api_key=api_key,
                action=f"Multimodal scan: {file_name}",
                target=file_name,
                result=report["verdict"],
                mode="red",
                risk_score=analysis["risk_score"],
                details={
                    "scan_id": report["scan_id"],
                    "injection_detected": analysis["injection_detected"],
                    "risk_level": analysis["risk_level"],
                    "findings_count": len(analysis["findings"]),
                },
            )
        except Exception as e:
            if console:
                console.print(f"[dim yellow]Audit log skipped: {e}[/dim yellow]")

    return report


def scan_multiple(
    image_paths: list,
    gemini_api_key: str = None,
    api_key: str = None,
) -> dict:
    """
    Scan multiple images and return a batch summary.
    """
    results = []
    for path in image_paths:
        result = scan_image(path, gemini_api_key=gemini_api_key, api_key=api_key)
        results.append(result)

    injections = [r for r in results if r.get("analysis", {}).get("injection_detected")]
    total_risk = sum(r.get("analysis", {}).get("risk_score", 0) for r in results)

    summary = {
        "batch_id": f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "total_images": len(results),
        "injections_found": len(injections),
        "avg_risk_score": round(total_risk / len(results), 3) if results else 0.0,
        "results": results,
    }

    # Save batch summary
    batch_path = REPORT_DIR / f"{summary['batch_id']}.json"
    batch_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if console:
        color = "red" if injections else "green"
        console.print(Panel(
            f"[bold]Total scanned:[/bold] {len(results)}\n"
            f"[bold]Injections found:[/bold] [{color}]{len(injections)}[/{color}]\n"
            f"[bold]Avg risk score:[/bold] {summary['avg_risk_score']}",
            title="Batch Scan Complete",
            border_style=color,
        ))

    return summary


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _verdict(analysis: dict) -> str:
    if not analysis["injection_detected"]:
        if analysis["suspicious"]:
            return "SUSPICIOUS"
        return "CLEAN"
    level = analysis["risk_level"]
    return f"INJECTION_DETECTED_{level}"


def _print_scan_result(report: dict):
    if not console:
        return
    analysis = report["analysis"]
    verdict = report["verdict"]
    color = {"CLEAN": "green", "SUSPICIOUS": "yellow"}.get(
        verdict, "red" if "CRITICAL" in verdict else "yellow"
    )

    console.print(Panel(
        f"[bold]Verdict:[/bold] [{color}]{verdict}[/{color}]\n"
        f"[bold]Risk Score:[/bold] {analysis['risk_score']}\n"
        f"[bold]Risk Level:[/bold] {analysis['risk_level']}\n"
        f"[bold]Injections found:[/bold] {len(analysis['findings'])}\n"
        f"[bold]Report:[/bold] {report['scan_id']}.json",
        title="Multimodal Injection Scan Result",
        border_style=color,
    ))

    if analysis["findings"]:
        console.print("\n[bold red]Injection Findings:[/bold red]")
        for f in analysis["findings"]:
            console.print(
                f"  [{f['severity']}] {f['label']} — "
                f"matched {f['match_count']}x — sample: \"{f['sample']}\""
            )

    if analysis["suspicious"]:
        console.print("\n[bold yellow]Suspicious Keywords:[/bold yellow]")
        for s in analysis["suspicious"]:
            console.print(f"  [{s['severity']}] {s['label']}")


# ── CLI / demo entry point ────────────────────────────────────────────────────

def main():
    """
    Interactive CLI for multimodal injection scanning.
    Run directly: python multimodal_injection.py
    """
    import sys

    # Load Gemini key from .env
    env_path = BASE_DIR / ".env"
    gemini_key = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                gemini_key = line.split("=", 1)[1].strip()

    # Load Spectrum admin key
    keys_path = BASE_DIR / "access_keys.json"
    api_key = "SPECTRUM-ADMIN-2026"

    if console:
        console.print("\n[bold cyan]🛡️  Spectrum Multimodal Injection Scanner[/bold cyan]")
        console.print("[dim]Detects hidden prompt injections in images[/dim]\n")

    if len(sys.argv) > 1:
        # Path(s) passed as arguments
        paths = sys.argv[1:]
    else:
        paths_input = input("Image path(s) [comma-separated] ❯ ").strip()
        paths = [p.strip() for p in paths_input.split(",") if p.strip()]

    if not paths:
        print("No paths provided.")
        return

    if len(paths) == 1:
        scan_image(paths[0], gemini_api_key=gemini_key, api_key=api_key)
    else:
        scan_multiple(paths, gemini_api_key=gemini_key, api_key=api_key)


if __name__ == "__main__":
    main()
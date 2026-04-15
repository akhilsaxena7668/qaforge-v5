import re
from typing import Dict, Any, Tuple

SUSPICIOUS_PATTERNS = {
    "eval_usage": r"\beval\s*\(",
    "exec_usage": r"\bexec\s*\(",
    "system_commands": r"\b(os\.system|subprocess\.|os\.popen)\s*\(",
    "base64_decode": r"b64decode\s*\(",
    "network_request": r"\b(urllib|requests\.(get|post)|http\.client)\s*",
    "reverse_shell": r"(nc\s+-e|bash\s+-i|/dev/tcp/|sh\s+-i)",
    "obfuscation": r"(\\x[0-9a-fA-F]{2}){4,}",
}

class AntivirusScanner:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        
    def scan_offline(self, content: str) -> Tuple[str, list]:
        findings = []
        for name, pattern in SUSPICIOUS_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(name)
                
        if len(findings) > 2:
            return "Malicious", findings
        elif len(findings) > 0:
            return "Suspicious", findings
        else:
            return "Safe", findings

    async def scan_hybrid(self, content: str, filename: str) -> Dict[str, Any]:
        offline_risk, offline_findings = self.scan_offline(content)
        
        # AI Scan
        prompt = f"""You are a Deep-Depth Antivirus and Security Expert.
Analyze the following file ({filename}) for any malicious behavior, vulnerabilities, backdoors, or suspicious logic.
Provide a concise 2-3 sentence analysis of exactly what this file does and whether it is safe.

FILE CONTENT:
'''
{str(content)[:15000]}  # type: ignore
'''
"""
        import asyncio
        try:
            # Run AI scan in thread pool since _try is sync
            ai_text, _ = await asyncio.to_thread(self.ai_engine._try, prompt, None, "flash")
        except Exception as e:
            ai_text = f"AI Scan failed to analyze: {str(e)}"
            
        combined_risk = offline_risk
        ai_lower = ai_text.lower()
        if combined_risk == "Safe":
            if "malicious" in ai_lower or "backdoor" in ai_lower or ("highly suspicious" in ai_lower):
                combined_risk = "Suspicious"
            elif offline_findings:
                combined_risk = "Suspicious"
                
        return {
            "filename": filename,
            "risk_level": combined_risk,
            "offline_findings": offline_findings,
            "ai_analysis": ai_text
        }

    async def scan_directory(self, dir_path: str) -> list[Dict[str, Any]]:
        import os
        from pathlib import Path
        
        results = []
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            return results
            
        IGNORE_EXTS = {'.exe', '.dll', '.bin', '.png', '.jpg', '.jpeg', '.mp4', '.mkv', '.pdf', '.zip', '.tar', '.gz'}
        MAX_SIZE = 5 * 1024 * 1024  # 5 MB
        
        # We will scan up to 1000 files to prevent total freezing
        file_count: int = 0
        
        for root, _, files in os.walk(p):
            for f in files:
                if file_count > 1000:
                    break
                
                fpath = Path(root) / f
                if fpath.suffix.lower() in IGNORE_EXTS: continue
                
                try:
                    if fpath.stat().st_size > MAX_SIZE: continue
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    
                    offline_risk, findings = self.scan_offline(content)
                    if offline_risk in ["Suspicious", "Malicious"]:
                        results.append({
                            "filepath": str(fpath),
                            "filename": f,
                            "risk_level": offline_risk,
                            "offline_findings": findings
                        })
                    file_count = file_count + 1
                except Exception:
                    pass
            if file_count > 1000:
                break
                
        return results

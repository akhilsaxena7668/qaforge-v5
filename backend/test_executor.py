"""QAForge Gemini — Test Executor (realistic simulation engine)"""

import asyncio, random
from datetime import datetime
from typing import Dict, Any, Optional

FAIL_RATES = {"critical": 0.04, "high": 0.09, "medium": 0.16, "low": 0.24}

DURATIONS = {
    "functional":  (600,  3200),
    "ui":          (400,  1800),
    "security":    (1200, 5500),
    "performance": (1800, 9000),
    "accessibility":(300, 1400),
    "api":         (150,  900),
    "usability":   (500,  2500),
}

FAIL_MSGS = {
    "functional":   ["Element not found: #submit-btn","Expected 200 OK, got 500","Form validation bypass succeeded","Session token not refreshed","Redirect loop detected on /checkout"],
    "ui":           ["Viewport overflow at 375px width","Z-index conflict on modal overlay","Font FOUT on slow connection","Tap target below 44×44px minimum","Color contrast 2.1:1 < WCAG AA 4.5:1"],
    "security":     ["XSS reflected in search param","CSRF token accepted after expiry","SQL error exposed in response","Missing X-Frame-Options header","JWT alg:none accepted"],
    "performance":  ["LCP 5.2s > 2.5s threshold","CLS 0.38 > 0.1 threshold","TBT 950ms > 200ms threshold","Memory leak: +180MB over 10 cycles","TTFB 2.8s on 3G throttle"],
    "accessibility":["<img> missing alt attribute","Modal focus not trapped","Keyboard nav skip-link broken","ARIA role mismatch on button","Form field missing aria-label"],
    "api":          ["Response 2400ms > 500ms SLA","Schema mismatch: missing `user_id`","Rate limit not enforced at 1k/min","Pagination cursor invalid after update","CORS wildcard on sensitive endpoint"],
    "usability":    ["Error message too technical for end user","No success feedback after form submit","Breadcrumb trail breaks on deep link","Back button loses scroll position"],
}

PASS_MSGS = [
    "All assertions passed within thresholds.",
    "Test completed successfully.",
    "Behavior matches specification.",
    "No regressions detected.",
    "Validation successful — all checks green.",
    "Expected outcome confirmed.",
]


class TestExecutor:
    async def run_test(self, test: Dict[str, Any], environment: str, base_url: Optional[str]) -> Dict[str, Any]:
        cat = test.get("category", "functional")
        pri = test.get("priority", "medium")
        lo, hi = DURATIONS.get(cat, (500, 2000))
        duration_ms = random.uniform(lo, hi)
        await asyncio.sleep(duration_ms / 12000)   # compressed simulation

        failed = random.random() < FAIL_RATES.get(pri, 0.15)
        steps  = test.get("steps", [])
        step_results = []
        fail_idx = len(steps) - 1 if steps else 0
        for i, s in enumerate(steps):
            is_fail = failed and i == fail_idx
            step_results.append({
                "step":     s.get("step", i + 1),
                "action":   s.get("action", ""),
                "expected": s.get("expected", ""),
                "status":   "fail" if is_fail else "pass",
                "note":     random.choice(FAIL_MSGS.get(cat, ["Unexpected error"])) if is_fail else "OK",
            })

        msgs = FAIL_MSGS.get(cat, ["Unexpected error"])
        status = "fail" if failed else "pass"
        return {
            "test_id":      test.get("id"),
            "test_name":    test.get("name"),
            "category":     cat,
            "priority":     pri,
            "severity":     test.get("severity", "major"),
            "status":       status,
            "actual_result": random.choice(msgs) if failed else random.choice(PASS_MSGS),
            "browser":      random.choice(["Chrome 122", "Firefox 124", "Safari 17.4", "Edge 122"]),
            "screen":       random.choice(["1920x1080", "1440x900", "390x844 (iPhone 15)", "1280x800"]),
            "duration_ms":  round(duration_ms),
            "environment":  environment,
            "executed_at":  datetime.now().isoformat(),
            "note":         random.choice(msgs) if failed else random.choice(PASS_MSGS),
            "steps":        step_results,
        }

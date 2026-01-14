import subprocess
import sys
import time
from typing import Tuple, List, Optional

def run_playwright_subprocess(script_path: str, disease: str, max_results: int, output_path: str,
                              timeout: Optional[int] = None) -> Tuple[int, float, List[str]]:
    """
    Run the Playwright scraper script as a subprocess and stream logs.
    Returns (returncode, elapsed_seconds, logs_lines)
    """
    cmd = [sys.executable, script_path, "--disease", disease, "--max_results", str(max_results), "--output", output_path, "--headless"]
    start = time.perf_counter()
    logs: List[str] = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    try:
        if proc.stdout is None:
            raise RuntimeError("Playwright process has no stdout")
        for line in proc.stdout:
            logs.append(line.rstrip("\n"))
            if timeout and (time.perf_counter() - start) > timeout:
                proc.kill()
                logs.append("Process killed due to timeout.")
                break
        proc.wait(timeout=5)
    except Exception as exc:
        try:
            proc.kill()
        except Exception:
            pass
        logs.append(f"Exception while running playwright scraper: {exc}")
    elapsed = time.perf_counter() - start
    return proc.returncode if proc.returncode is not None else -1, elapsed, logs
from __future__ import annotations

import os
import subprocess
import sys


def check_missing_key(binary_path: str) -> None:
    result = subprocess.run(
        [binary_path],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 1:
        raise SystemExit(
            f"expected exit code 1 with no API key, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if "REJESTR_IO_API_KEY environment variable is required" not in result.stderr:
        raise SystemExit(f"missing expected error message in stderr: {result.stderr}")


def check_starts_with_key(binary_path: str) -> None:
    env = dict(os.environ)
    env["REJESTR_IO_API_KEY"] = "smoke-test-key"
    # Feeding empty stdin closes it immediately, which the server treats as a
    # hard error once it tries to read a request. That's fine here: we only
    # care that it gets far enough to log the startup line before dying, not
    # that it survives an immediately-closed stdin (a real MCP client keeps
    # stdin open).
    result = subprocess.run(
        [binary_path],
        input="",
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    combined = result.stdout + result.stderr
    if "Starting MCP server" not in combined:
        raise SystemExit(f"binary did not report starting the MCP server:\n{combined}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_test.py <path-to-binary>")
    binary_path = sys.argv[1]
    check_missing_key(binary_path)
    check_starts_with_key(binary_path)
    print("Smoke test passed.")


if __name__ == "__main__":
    main()

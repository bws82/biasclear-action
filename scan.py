#!/usr/bin/env python3
"""
BiasClear GitHub Action — Scan Script

Scans files matching a glob pattern for structural bias using BiasClear.
Outputs results as GitHub Actions step outputs and annotations.
Fails the workflow if any file's truth score drops below the threshold.
"""

import glob
import json
import os
import sys
import asyncio


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


async def main():
    paths_pattern = get_env("SCAN_PATHS", "**/*.md")
    threshold = int(get_env("SCAN_THRESHOLD", "70"))
    domain = get_env("SCAN_DOMAIN", "general")
    fail_on_bias = get_env("SCAN_FAIL_ON_BIAS", "true").lower() == "true"

    # Find files matching the glob pattern
    files = glob.glob(paths_pattern, recursive=True)

    if not files:
        print(f"::notice::No files matched pattern '{paths_pattern}'")
        _set_output("total_files", "0")
        _set_output("flagged_files", "0")
        _set_output("avg_score", "100")
        _set_output("report", "[]")
        return

    print(f"🔍 BiasClear scanning {len(files)} file(s) in domain '{domain}'")
    print(f"   Threshold: {threshold} | Fail on bias: {fail_on_bias}")
    print(f"   Pattern: {paths_pattern}")
    print()

    # Import BiasClear
    from biasclear.detector import scan_local

    results = []
    flagged = []
    total_score = 0

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            if not text.strip():
                print(f"  ⏭ {filepath} (empty, skipped)")
                continue

            # Scan the file
            result = await scan_local(text, domain=domain)
            score = result.get("truth_score", 100)
            flags = result.get("flags", [])
            bias_detected = result.get("bias_detected", False)
            flag_count = len(flags)
            total_score += score

            file_result = {
                "file": filepath,
                "truth_score": score,
                "bias_detected": bias_detected,
                "flag_count": flag_count,
                "flags": [
                    {"name": f.get("name", ""), "severity": f.get("severity", "")}
                    for f in flags[:5]
                ],
            }
            results.append(file_result)

            # Output formatting
            if bias_detected or score < threshold:
                flagged.append(file_result)
                status = "🔴"
                # Create GitHub annotation
                flag_names = ", ".join(f.get("name", "") for f in flags[:3])
                print(f"::warning file={filepath}::"
                      f"BiasClear: score {score}/100, "
                      f"{flag_count} pattern(s) detected: {flag_names}")
            elif score < 90:
                status = "🟡"
            else:
                status = "🟢"

            print(f"  {status} {filepath}: score {score}, "
                  f"{flag_count} flag(s)")

        except Exception as e:
            print(f"  ⚠️  {filepath}: scan failed ({e})")
            results.append({
                "file": filepath,
                "error": str(e),
                "skipped": True,
            })

    # Summary
    scanned = [r for r in results if not r.get("skipped")]
    avg_score = round(total_score / max(len(scanned), 1), 1) if scanned else 100

    print()
    print("━" * 60)
    print(f"📊 BiasClear Results: {len(scanned)} scanned, "
          f"{len(flagged)} flagged, avg score {avg_score}")
    print("━" * 60)

    # Set outputs
    _set_output("total_files", str(len(scanned)))
    _set_output("flagged_files", str(len(flagged)))
    _set_output("avg_score", str(avg_score))
    _set_output("report", json.dumps(results, default=str))

    # Create job summary
    summary = _build_summary(scanned, flagged, avg_score, threshold, domain)
    _write_summary(summary)

    # Fail if flagged and configured to fail
    if flagged and fail_on_bias:
        below = [f for f in flagged if f.get("truth_score", 100) < threshold]
        if below:
            print(f"\n❌ {len(below)} file(s) scored below threshold ({threshold})")
            sys.exit(1)

    print("\n✅ All files passed BiasClear scan")


def _set_output(name: str, value: str):
    """Set a GitHub Actions step output."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            # Handle multiline values
            if "\n" in value:
                import uuid
                delimiter = uuid.uuid4().hex
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    else:
        # Local testing fallback
        print(f"  [output] {name}={value[:100]}{'...' if len(value) > 100 else ''}")


def _build_summary(
    scanned: list, flagged: list, avg_score: float,
    threshold: int, domain: str
) -> str:
    """Build a GitHub Actions job summary in markdown."""
    lines = [
        "## 🔍 BiasClear Scan Results",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Files scanned | {len(scanned)} |",
        f"| Files flagged | {len(flagged)} |",
        f"| Average truth score | {avg_score}/100 |",
        f"| Threshold | {threshold} |",
        f"| Domain | {domain} |",
        "",
    ]

    if flagged:
        lines.append("### ⚠️ Flagged Files")
        lines.append("")
        lines.append("| File | Score | Flags |")
        lines.append("|------|-------|-------|")
        for f in flagged:
            flag_names = ", ".join(
                fl.get("name", "") for fl in f.get("flags", [])[:3]
            )
            lines.append(f"| `{f['file']}` | {f['truth_score']} | {flag_names} |")
        lines.append("")

    if not flagged:
        lines.append("### ✅ All files passed")
        lines.append("")

    lines.append("---")
    lines.append("*Powered by [BiasClear](https://github.com/bws82/biasclear) — "
                  "structural bias detection built on Persistent Influence Theory*")

    return "\n".join(lines)


def _write_summary(summary: str):
    """Write to GitHub Actions job summary."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(summary + "\n")
    else:
        print("\n" + summary)


if __name__ == "__main__":
    asyncio.run(main())

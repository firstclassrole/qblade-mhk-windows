"""Read-only coverage audit of a native XFOIL/QBlade finite-angle polar.

Reports missing requested angles and coefficient support, not convergence.
No interpolation, solver run, polar repair, or source modification is performed.
Python3.10+, standard library only.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def read_polar(path):
    text = path.read_text(encoding="utf-8-sig")
    rows = []
    started = False
    column_count = None
    for number, line in enumerate(text.splitlines(), 1):
        parts = line.split()
        if len(parts) >= 3 and [p.lower() for p in parts[:3]] == ["alpha", "cl", "cd"]:
            if started:
                raise ValueError("multiple polar tables are not supported")
            started, column_count = True, len(parts)
            continue
        if not started or not parts or all(set(p) <= {"-"} for p in parts):
            continue
        try:
            values = [float(p.replace("D", "E").replace("d", "e")) for p in parts]
        except ValueError as exc:
            raise ValueError(f"unreadable polar row at line{number}") from exc
        if len(values) != column_count:
            raise ValueError(f"column count differs at line{number}")
        if not math.isfinite(values[0]):
            raise ValueError(f"nonfinite angle at line{number}")
        rows.append({"alpha": values[0],
                     "CL": values[1] if math.isfinite(values[1]) else None,
                     "CD": values[2] if math.isfinite(values[2]) else None,
                     "all_values_finite": all(math.isfinite(v) for v in values), "source_line": number})
    if not started or not rows:
        raise ValueError("no supported nonempty alpha/CL/CD table")
    return rows


def audit(path, alpha_min, alpha_max, alpha_step, check_angles):
    if not all(math.isfinite(v) for v in [alpha_min, alpha_max, alpha_step, *check_angles]):
        raise ValueError("requested angles must be finite")
    if alpha_step <= 0 or alpha_max < alpha_min:
        raise ValueError("require positive step and max>=min")
    intervals = (alpha_max - alpha_min) / alpha_step
    if not math.isclose(intervals, round(intervals), rel_tol=0, abs_tol=1e-8):
        raise ValueError("range must contain an integral number of steps")
    if intervals > 100000:
        raise ValueError("requested grid is too large")
    rows = read_polar(path)
    tolerance = max(1e-8, alpha_step * 1e-6)
    requested = [alpha_min + i * alpha_step for i in range(round(intervals) + 1)]
    def matches(angle):
        return [r for r in rows if abs(r["alpha"] - angle) <= tolerance]
    missing = [a for a in requested if not matches(a)]
    counts = Counter(r["alpha"] for r in rows)
    valid = [r for r in rows if r["all_values_finite"] and r["CD"] > 0]
    best = max(valid, key=lambda r: r["CL"] / r["CD"], default=None)
    if best is not None:
        best = {**best, "L_over_D": best["CL"] / best["CD"],
                "at_requested_endpoint": any(abs(best["alpha"]-a) <= tolerance for a in (alpha_min, alpha_max)),
                "requested_grid_neighbors_present": all(bool(matches(best["alpha"]+d*alpha_step)) for d in (-1, 1))}
    return {
        "file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "requested_points": len(requested), "saved_rows": len(rows),
        "requested_angles_with_saved_support": len(requested)-len(missing),
        "missing_angles_deg": missing,
        "duplicate_exact_angles_deg": [a for a, count in counts.items() if count > 1],
        "nonfinite_coefficient_rows": [r["source_line"] for r in rows if not r["all_values_finite"]],
        "nonpositive_CD_rows": [r["source_line"] for r in rows if r["CD"] is not None and r["CD"] <= 0],
        "checked_angles": [{"alpha_deg": a, "saved_rows": matches(a)} for a in check_angles],
        "maximum_saved_L_over_D": best,
        "interpretation": "Saved coverage only. Maximum is not certified optimum. No convergence, branch continuity, transition or experimental validity is established.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=Path, nargs="+")
    parser.add_argument("--alpha-min", type=float, required=True)
    parser.add_argument("--alpha-max", type=float, required=True)
    parser.add_argument("--alpha-step", type=float, required=True)
    parser.add_argument("--check-alpha", type=float, nargs="*", default=[])
    args = parser.parse_args()
    try:
        reports = [audit(p, args.alpha_min, args.alpha_max, args.alpha_step, args.check_alpha) for p in args.files]
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"Audit failed: {exc}\n")
    print(json.dumps(reports, ensure_ascii=False, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()

"""Extract a verified ten-array Rotor BEM record from a QBlade QPR copy.

This is a deliberately narrow, empirical reader for archive format 310043,
observed in QBlade CE 2.0.9.7b_beta Windows, not a general QPR parser.
It never changes the source project.  The record layout was identified in the
supplied QBlade 2.0.9 project and is accepted only after several independent
physical identities pass.  An exact Qt QString object name locates candidates;
hard-coded offsets are not used for extraction.

Example (PowerShell):
  python extract_qpr_bem.py PROJECT --object-name EXACT_NAME --prefix CASE --rho 1000 --rotor-radius 0.25 --hub-radius 0.05

For a later saved case, use its exact simulation name.  First use --locate-only
to inspect all name occurrences and validated block candidates.  A changed
serialization schema fails explicitly instead of guessing an array mapping.
"""

import argparse
import csv
import hashlib
import json
import math
import statistics
import struct
from pathlib import Path


FIELDS = (
    "Cp", "Ct", "Cq", "TSR", "power_W", "axial_thrust_N",
    "inflow_m_per_s", "rotor_speed_rpm",
    "saved_blade_bending_unverified_Nm", "shaft_torque_Nm",
)
UNITS = ("1", "1", "1", "1", "W", "N", "m/s", "rpm", "N m (interpretation unverified)", "N m")


def relative_error(a, b, floor=1e-12):
    return abs(a - b) / max(abs(a), abs(b), floor)


def read_candidate(blob, start):
    """Read 10 equal-length <uint32 count, count*float32> lists safely."""
    cursor = start
    columns, mapping = {}, []
    count = None
    for index, (name, unit) in enumerate(zip(FIELDS, UNITS)):
        if cursor < 0 or cursor + 4 > len(blob):
            raise ValueError("count lies outside source")
        n = struct.unpack_from("<I", blob, cursor)[0]
        if not 3 <= n <= 10000 or (count is not None and n != count):
            raise ValueError("ten list counts do not agree or are implausible")
        count = n
        end = cursor + 4 + 4 * count
        if end > len(blob):
            raise ValueError("array extends outside source")
        values = list(struct.unpack_from(f"<{count}f", blob, cursor + 4))
        if not all(math.isfinite(v) for v in values):
            raise ValueError("nonfinite array value")
        columns[name] = values
        mapping.append({
            "array_index_zero_based": index, "field": name, "units": unit,
            "count_offset_bytes_zero_based": cursor,
            "count_storage": "uint32 little-endian", "count": count,
            "values_offset_bytes_zero_based": cursor + 4,
            "values_storage": "IEEE 754 float32 little-endian",
            "end_offset_bytes_exclusive": end,
        })
        cursor = end
    tsr = columns["TSR"]
    if not all(x > 0 for x in tsr) or not all(b > a for a, b in zip(tsr, tsr[1:])):
        raise ValueError("TSR is not positive and strictly increasing")
    if max(relative_error(cp, lam * cq) for cp, lam, cq in zip(columns["Cp"], tsr, columns["Cq"])) > 2e-5:
        raise ValueError("Cp = TSR * Cq failed")
    omega = [rpm * 2 * math.pi / 60 for rpm in columns["rotor_speed_rpm"]]
    if not all(w > 0 for w in omega) or not all(u > 0 for u in columns["inflow_m_per_s"]):
        raise ValueError("nonpositive inflow or rotation speed")
    if max(relative_error(p, w * q) for p, w, q in zip(columns["power_W"], omega, columns["shaft_torque_Nm"])) > 2e-5:
        raise ValueError("P = omega * Q failed")
    radii = [lam * u / w for lam, u, w in zip(tsr, columns["inflow_m_per_s"], omega)]
    if max(radii) / min(radii) - 1 > 2e-5:
        raise ValueError("TSR, inflow and rpm do not imply one rotor radius")
    return columns, mapping, cursor


def locate(blob, name):
    """Require an exact length-prefixed UTF-16LE QString and validated data."""
    needle = name.encode("utf-16le")
    occurrences, candidates = [], []
    pos = 0
    while True:
        pos = blob.find(needle, pos)
        if pos < 0:
            break
        entry = {"name_offset_bytes_zero_based": pos}
        if pos >= 4:
            entry["preceding_uint32"] = struct.unpack_from("<I", blob, pos - 4)[0]
        if pos >= 4 and entry["preceding_uint32"] == len(needle):
            entry["qt_qstring_length_matches"] = True
            start = pos + len(needle)
            try:
                cols, mapping, end = read_candidate(blob, start)
                entry.update({"validated_ten_array_record": True, "record_start": start, "record_end_exclusive": end})
                candidates.append((entry, cols, mapping))
            except (ValueError, struct.error) as exc:
                entry.update({"validated_ten_array_record": False, "rejection": str(exc)})
        else:
            entry["qt_qstring_length_matches"] = False
        occurrences.append(entry)
        pos += max(1, len(needle))
    return occurrences, candidates


def describe(values):
    return {"count": len(values), "minimum": min(values), "median": statistics.median(values), "maximum": max(values)}


def make_audit(path, blob, args, selected, occurrences, columns, mapping):
    n = len(columns["TSR"])
    rows = [dict(zip(FIELDS, values)) for values in zip(*(columns[f] for f in FIELDS))]
    omega = [r["rotor_speed_rpm"] * 2 * math.pi / 60 for r in rows]
    cp_res = [r["Cp"] - r["TSR"] * r["Cq"] for r in rows]
    cp_rel = [relative_error(r["Cp"], r["TSR"] * r["Cq"]) for r in rows]
    p_res = [r["power_W"] - w * r["shaft_torque_Nm"] for r, w in zip(rows, omega)]
    p_rel = [relative_error(r["power_W"], w * r["shaft_torque_Nm"]) for r, w in zip(rows, omega)]
    radii = [r["TSR"] * r["inflow_m_per_s"] / w for r, w in zip(rows, omega)]
    cp_threshold, ct_threshold = 1e-6, 1e-6
    area_p = [(i, r["power_W"] / (0.5 * args.rho * r["inflow_m_per_s"]**3 * r["Cp"])) for i, r in enumerate(rows) if abs(r["Cp"]) > cp_threshold]
    area_t = [(i, r["axial_thrust_N"] / (0.5 * args.rho * r["inflow_m_per_s"]**2 * r["Ct"])) for i, r in enumerate(rows) if abs(r["Ct"]) > ct_threshold]
    area_q = [(i, r["shaft_torque_Nm"] / (0.5 * args.rho * r["inflow_m_per_s"]**2 * args.rotor_radius * r["Cq"])) for i, r in enumerate(rows) if abs(r["Cq"]) > 1e-6]
    disk = math.pi * args.rotor_radius**2
    annulus = math.pi * (args.rotor_radius**2 - args.hub_radius**2)
    max_area_err = max(abs(v - disk) / disk for pairs in (area_p, area_t, area_q) for _, v in pairs)
    if max_area_err > 2e-5:
        raise ValueError("dimensional arrays do not consistently imply the supplied full disk reference area; review geometry and density")
    if max(abs(v - args.rotor_radius) / args.rotor_radius for v in radii) > 2e-5:
        raise ValueError("rpm/TSR imply a different rotor tip radius")
    peak_specs = {
        "maximum_power": ("power_W", lambda r: r["power_W"]),
        "maximum_positive_shaft_torque": ("shaft_torque_Nm", lambda r: r["shaft_torque_Nm"]),
        "maximum_absolute_shaft_torque": ("shaft_torque_Nm", lambda r: abs(r["shaft_torque_Nm"])),
        "maximum_axial_thrust": ("axial_thrust_N", lambda r: r["axial_thrust_N"]),
        "maximum_saved_bending_unverified": ("saved_blade_bending_unverified_Nm", lambda r: r["saved_blade_bending_unverified_Nm"]),
        "minimum_power": ("power_W", lambda r: -r["power_W"]),
        "minimum_shaft_torque": ("shaft_torque_Nm", lambda r: -r["shaft_torque_Nm"]),
    }
    peaks = {}
    for title, (field, key) in peak_specs.items():
        i = max(range(n), key=lambda j: key(rows[j]))
        peaks[title] = {"selection_field": field, "source_row_index_zero_based": i, **rows[i]}
    audit = {
        "purpose": "Read-only extraction of saved Rotor BEM arrays for independent data auditing; no source project was edited.",
        "extractor": "extract_qpr_bem.py; empirical ten-array schema, not a general QPR deserializer",
        "source": {"absolute_path": str(path), "byte_count": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "archive_first_uint32_little_endian": struct.unpack_from("<I", blob, 0)[0]},
        "object": {"exact_name": args.object_name, "qstring_encoding": "UTF-16LE with preceding uint32 byte length", "qstring_length_prefix_offset_bytes_zero_based": selected["name_offset_bytes_zero_based"] - 4, **selected},
        "name_occurrence_count": len(occurrences),
        "validated_record_count_for_exact_name": sum(bool(x.get("validated_ten_array_record")) for x in occurrences),
        "array_mapping": mapping,
        "record_boundary_warning": "The uint32 count immediately after the ten arrays belongs to following saved operating-point objects; it must not be decoded as an eleventh float array.",
        "range": {"saved_rows": n, "first_TSR": columns["TSR"][0], "last_TSR": columns["TSR"][-1], "median_TSR_step": statistics.median(b-a for a, b in zip(columns["TSR"], columns["TSR"][1:])), "inflow_m_per_s": describe(columns["inflow_m_per_s"])},
        "geometry_and_density_inputs": {"density_kg_per_m3": args.rho, "rotor_tip_radius_m": args.rotor_radius, "hub_radius_m": args.hub_radius, "blade_count_from_UI": args.blade_count, "blade_span_m_from_UI": args.rotor_radius - args.hub_radius, "provenance": "Geometry supplied from QBlade UI observation; density supplied by CLI and checked against saved load normalization."},
        "identity_checks_all_saved_rows": {
            "Cp_equals_TSR_times_Cq": {"maximum_absolute_residual": max(map(abs, cp_res)), "maximum_relative_residual": max(cp_rel), "rows_checked": n, "passed_relative_tolerance_2e_minus_5": max(cp_rel) <= 2e-5},
            "power_equals_omega_times_shaft_torque": {"maximum_absolute_residual_W": max(map(abs, p_res)), "maximum_relative_residual": max(p_rel), "rows_checked": n, "passed_relative_tolerance_2e_minus_5": max(p_rel) <= 2e-5},
            "tip_radius_from_TSR_U_rpm_m": describe(radii),
        },
        "reference_area_checks": {
            "formulas": {"from_power": "A = P / (0.5 * rho * U^3 * Cp)", "from_axial_thrust": "A = T / (0.5 * rho * U^2 * Ct)", "from_shaft_torque": "A = Q / (0.5 * rho * U^2 * Rtip * Cq)"},
            "well_conditioned_selection": {"absolute_Cp_greater_than": cp_threshold, "absolute_Ct_greater_than": ct_threshold, "absolute_Cq_greater_than": 1e-6},
            "area_from_power_m2": describe([v for _, v in area_p]),
            "area_from_thrust_m2": describe([v for _, v in area_t]),
            "area_from_torque_m2": describe([v for _, v in area_q]),
            "full_disk_pi_Rtip_squared_m2": disk,
            "annulus_pi_Rtip_squared_minus_Rhub_squared_m2": annulus,
            "maximum_relative_error_against_full_disk_all_well_conditioned_rows": max_area_err,
            "passed_full_disk_relative_tolerance_2e_minus_5": max_area_err <= 2e-5,
            "conclusion": "These saved dimensional loads use the full disk reference area. The UI annulus area must not be substituted when reconstructing loads from these coefficients.",
            "per_row_area_evidence": [{"source_row_index_zero_based": i, "area_from_power_m2": dict(area_p).get(i), "area_from_thrust_m2": dict(area_t).get(i), "area_from_torque_m2": dict(area_q).get(i)} for i in range(n)],
        },
        "extrema": peaks,
        "field_correspondence_and_limits": [
            "Cp, Ct, Cq, TSR, power, axial thrust, inflow, rpm and shaft torque are independently cross-checked by dimensionless and dimensional identities. Float32 rounding is retained.",
            "Array 8 is named saved_blade_bending_unverified_Nm. Its interpretation as blade-root bending or shaft bending has not been confirmed and it must not be used as either directly.",
            "Historical QBlade BEMData.cpp saved a per-blade normal-force radial moment about rotor center. The current ambiguous saved field resembles that structure, but historical source is not proof of the current field's exact reference or units.",
            "The ten-array order is structurally consistent with the historical BEMData serialization after omitted inverse-lambda and Kp arrays; the current binary layout is verified empirically, not claimed identical to historical source.",
            "Power and shaft torque are signed. Negative values at high TSR are preserved rather than clipped or converted to absolute values.",
            "These are saved simulation results. Current simulation editor range entries do not overwrite the stored TSR range.",
            f"The saved geometry has {args.hub_radius:g} m hub radius and {args.rotor_radius:g} m tip radius. These loads must not be transferred to a differently sized STL or modified rotor without resimulation.",
        ],
        "historical_crosscheck_sources_not_current_schema_authority": [
            "https://raw.githubusercontent.com/rmaugusto/qblade/master/src/XBEM/BData.cpp",
            "https://raw.githubusercontent.com/rmaugusto/qblade/master/src/XBEM/BEMData.cpp",
        ],
        "later_project_recipe": [
            "Save the later simulation into a separate project copy in QBlade and record its exact simulation object name.",
            "Run this script with that project, --object-name EXACT_NAME and a new --prefix. Use --locate-only first to inspect candidates without writing CSV/JSON.",
            "The script finds all exact UTF-16LE name occurrences and checks the preceding Qt QString byte length. Only a unique occurrence followed by ten matching-count finite float32 arrays and valid Cp/TSR/Cq plus P/omega/Q identities is accepted.",
            "Supply the later case's actual --rho, --rotor-radius and --hub-radius. Full disk normalization and inferred tip radius must agree within the float32 tolerance. If a layout or identity changes, stop and investigate; do not reuse byte offsets blindly.",
            "Compare source SHA256, array offsets, saved count/range, dimensional values and extrema with QBlade UI or an official export before relying on a later project.",
        ],
    }
    return audit, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--module", choices=("hawt-rotor-bem",), required=True, help="Only verified HAWT Rotor BEM is supported; not DMS/AC or VAWT")
    parser.add_argument("--object-name", required=True)
    parser.add_argument("--prefix", default="saved_bem")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--rho", type=float, required=True)
    parser.add_argument("--rotor-radius", type=float, required=True)
    parser.add_argument("--hub-radius", type=float, required=True)
    parser.add_argument("--blade-count", type=int)
    parser.add_argument("--locate-only", action="store_true")
    args = parser.parse_args()
    path = args.source.resolve(strict=True)
    if not (args.rho > 0 and args.rotor_radius > args.hub_radius >= 0):
        parser.error("require positive density and Rtip > Rhub >= 0")
    if Path(args.prefix).name != args.prefix or args.prefix in (".", ".."):
        parser.error("prefix must be a filename component")
    blob = path.read_bytes()
    if len(blob) < 4 or struct.unpack_from("<I", blob, 0)[0] != 310043:
        raise SystemExit("Unsupported QPR archive header: this empirical extractor accepts only format 310043. Use a native QBlade export or investigate the new serialization schema.")
    if args.blade_count is not None and args.blade_count < 1:
        parser.error("blade count must be positive when supplied")
    occurrences, candidates = locate(blob, args.object_name)
    if args.locate_only:
        print(json.dumps({"source_sha256": hashlib.sha256(blob).hexdigest(), "object_name": args.object_name, "occurrences": occurrences}, indent=2))
        return
    if len(candidates) != 1:
        raise SystemExit(f"Require exactly one validated ten-array record for {args.object_name!r}; found {len(candidates)}. Use --locate-only.")
    selected, columns, mapping = candidates[0]
    audit, rows = make_audit(path, blob, args, selected, occurrences, columns, mapping)
    audit["declared_module"] = args.module
    audit["module_scope_limit"] = "The caller must verify HAWT Rotor BEM in QBlade. Header and array identities do not independently establish module type; DMS/VAWT are unsupported."
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{args.prefix}_saved_bem.csv"
    audit_path = out_dir / f"{args.prefix}_extraction_audit.json"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("source_row_index_zero_based", *FIELDS))
        writer.writeheader()
        for i, row in enumerate(rows):
            writer.writerow({"source_row_index_zero_based": i, **row})
    audit["outputs"] = {"raw_csv_absolute_path": str(csv_path), "audit_json_absolute_path": str(audit_path)}
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"csv": str(csv_path), "audit": str(audit_path), "source_sha256": audit["source"]["sha256"], "rows": len(rows), "record_start": selected["record_start"], "record_end_exclusive": selected["record_end_exclusive"], "max_full_disk_area_relative_error": audit["reference_area_checks"]["maximum_relative_error_against_full_disk_all_well_conditioned_rows"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

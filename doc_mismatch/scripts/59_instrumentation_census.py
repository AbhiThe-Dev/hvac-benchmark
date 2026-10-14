"""Instrumentation census of the 45 Mortar Brick models: which connection types could each building's recorded points ever support? Metadata only -- no timeseries is read,
nothing is fitted or scored.

  .venv/bin/python doc_mismatch/scripts/59_instrumentation_census.py     ->  results/docmismatch/intake/mortar_census.md

RECORDED = the point links to a timeseries; DOCUMENTED = the graph lists it. A channel is SUPPORTED in a building when >= 80% of its documented pairs have every point that channel
reads (the readiness report's rule and channel-needs table). The ORNL building is not part of this census (a different graph family).
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results" / "docmismatch" / "intake" / "mortar_census.md"
WATER = ("Pump", "Valve", "Loop", "Boiler", "Chiller", "Water_System", "Coil")


def pct(a, b):
    return f"{a / b:.0%}" if b else "n/a"


def main():
    allc = [C.parse_census(f) for f in sorted((REPO / "data_cache").glob("mortar__*.ttl"))]
    cen, dup = C.distinct(allc)
    n = len(cen)
    md = ["# Instrumentation census of the Mortar Brick models (metadata only)", "",
          f"{len(allc)} graphs, {n} distinct buildings" + (" (" + "; ".join(f"`{d}` lists the same streams as `{k}`" for d, k in dup) + ")" if dup else "") + ". "
          "RECORDED = the point links to a timeseries; DOCUMENTED = the graph lists it. A channel is SUPPORTED in a building when >= 80% of its documented pairs have every point the channel reads "
          "(same rule and channel-needs table as the readiness report). Nothing here reads a timeseries; whether a linked stream actually holds usable data is a separate question (readiness).", ""]

    # 1. what kinds of things are modelled
    kind_b = {k: sum(1 for c in cen if any(v == k for v in c.kinds.values())) for k in ("AHU", "VAV", "Zone", "Coil")}
    water = Counter()
    for c in cen:
        for cls, m in c.classes.items():
            if any(w in cls for w in WATER):
                water[cls] += 1
    md += ["## What is modelled", "", f"- Buildings with AHUs: {kind_b['AHU']}; with VAV boxes: {kind_b['VAV']}; with zones: {kind_b['Zone']}; with coils as nodes: {kind_b['Coil']} of {n}.",
           "- Water-side node classes present, by number of buildings: " + (", ".join(f"{k} ({v})" for k, v in water.most_common(8)) or "none") +
           ". There is no water loop, branch, valve or pump node in any graph, so `loop_branch`, `branch_coil`, `loop_pump` and `loop_source` cannot be tested on this dataset at all.", ""]

    # 2. connection types
    md += ["## Which connection types could be tested", "",
           "Buildings (of the ones that document the connection) supporting each channel; 'recorded' counts only points with a timeseries, 'if trended' counts every documented point.", "",
           "| connection | buildings documenting it | documented pairs | ch0 | ch1 | ch2 | all 3 channels | at least one channel | at least one channel, if every documented point were trended |",
           "|---|---|---|---|---|---|---|---|---|"]
    per = {}
    for slot in C.SLOTS:
        rows = []
        for c in cen:
            r, d = C.channel_shares(c, slot, True), C.channel_shares(c, slot, False)
            if r["n_pairs"]:
                rows.append((c, r, d))
        per[slot] = rows
        m = len(rows)
        s = lambda k: sum(C.supports(r, k) for _, r, _ in rows)  # noqa: E731
        allthree = sum(all(C.supports(r, k) for k in range(3)) for _, r, _ in rows)
        anyc = sum(any(C.supports(r, k) for k in range(3)) for _, r, _ in rows)
        anyd = sum(any(C.supports(d, k) for k in range(3)) for _, _, d in rows)
        pairs = sum(r["n_pairs"] for _, r, _ in rows)
        md.append(f"| {slot} | {m} | {pairs} | {s(0)} | {s(1)} | {s(2)} | {allthree} | {anyc} | {anyd} |")
    md += ["", "Pair level (all buildings together): the share of documented pairs whose two ends have every point a channel reads (recorded / if trended).", "", "| connection | pairs | ch0 | ch1 | ch2 |", "|---|---|---|---|---|"]
    for slot in C.SLOTS:
        rows = per[slot]
        tot = sum(r["n_pairs"] for _, r, _ in rows)
        cell = lambda k: f"{pct(sum(r['channels'][k] * r['n_pairs'] for _, r, _ in rows), tot)} / {pct(sum(d['channels'][k] * d['n_pairs'] for _, _, d in rows), tot)}"  # noqa: E731
        md.append(f"| {slot} | {tot} | {cell(0)} | {cell(1)} | {cell(2)} |")
    md.append("")

    # 3. roles
    md += ["## Which measurements exist", "", "Per equipment kind and signal: buildings where at least one item has it recorded, and where at least 80% of the items do (documented-only in brackets).", "",
           "| equipment | signal | at least one recorded | >= 80% recorded | at least one documented | >= 80% documented |", "|---|---|---|---|---|---|"]
    for (kind, sig) in C.ROLE_CLASSES:
        def cov(recorded):
            some = full = 0
            for c in cen:
                nodes = [k for k, v in c.kinds.items() if v == kind]
                if not nodes:
                    continue
                have = sum(C.has_role(c, k, kind, sig, recorded) for k in nodes)
                some += have > 0
                full += have >= 0.8 * len(nodes)
            return some, full
        (s1, f1), (s2, f2) = cov(True), cov(False)
        md.append(f"| {kind} | {sig} | {s1} | {f1} | {s2} | {f2} |")
    md.append("")

    # 4. measured but unused
    used = {cls for classes in C.ROLE_CLASSES.values() for cls in classes}
    md += ["## What real buildings record that our channels do not use", "", "Point classes with a timeseries, by number of buildings, on AHUs, VAV boxes and zones (classes our channels already read are left out).", ""]
    for kind in ("AHU", "VAV", "Zone"):
        bld = Counter()
        pts = Counter()
        for c in cen:
            seen = set()
            for node, kk in c.kinds.items():
                if kk != kind:
                    continue
                for cls, ts in c.points.get(node, []):
                    if ts and cls not in used:
                        pts[cls] += 1
                        seen.add(cls)
            bld.update(seen)
        md.append(f"- **{kind}**: " + ", ".join(f"{cls} ({bld[cls]} buildings, {pts[cls]} points)" for cls, _ in bld.most_common(12)))
    md.append("")

    # 5. per building
    md += ["## Per building (recorded points; share of documented pairs each channel can use)", "", "| building | AHU->VAV pairs | ahu_vav ch0 / ch1 / ch2 | VAV->zone pairs | vav_zone ch0 / ch1 / ch2 |", "|---|---|---|---|---|"]
    for c in cen:
        a, z = C.channel_shares(c, "ahu_vav"), C.channel_shares(c, "vav_zone")
        if not (a["n_pairs"] or z["n_pairs"]):
            continue
        f = lambda r: "-" if not r["n_pairs"] else " / ".join(f"{r['channels'][k]:.0%}" for k in range(3))  # noqa: E731
        md.append(f"| {c.building} | {a['n_pairs']} | {f(a)} | {z['n_pairs']} | {f(z)} |")
    OUT.write_text("\n".join(md))
    print("\n".join(md))


main()

# Does "T3-noattr" hold up against the language model? (Exploratory note E2, extended)

`T3-noattr` = T1's items (equipment list, drawings' claims) plus `bas_access` and `point_map`, but no `attributes` -- the item set built in Exploratory note E2 from the user's reported field finding (BAS access and a point map common, documented attributes rare). This replays the routine (`tool_ticket_memo2`) at that item set on the exact 30 visits Addendum 33 already ran the language model on (same world, same `TableOracle` answers); the language model's own numbers are Addendum 33's stored ones, unchanged -- no new language model call. Simulation only; a language model is not a technician; the 30-visit sample is small (wide intervals); every minute and probability a placeholder.

## Minutes / accuracy / wrong-and-confident / checks (all visits, kind shares reweighted)

| policy | minutes | accuracy | wrong-and-confident | checks |
|---|---|---|---|---|
| LLM technician, T2 | 76.2 | 82% | 16.1% | 8.8 |
| LLM technician, T3 | 75.9 | 79% | 5.0% | 16.3 |
| routine, T2 (attributes, no access) | 92.0 | 84% | 0.3% | 9.5 |
| routine, T3 (attributes + access + map) | 57.9 | 87% | 0.3% | 11.3 |
| routine, T3-noattr (access + map, no attributes) | 68.1 | 89% | 0.3% | 11.3 |

## Paired comparisons (routine@T3-noattr minus the other side; all visits, kind shares reweighted)

| comparison | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label |
|---|---|---|---|---|---|
| T3-noattr vs LLM@T2  [T3-noattr's speed win over the LLM's own faster pilot tier] | -8.2 (-11%) | +0.069 | -0.158 | SAME / SAME | NEITHER |
| T3-noattr vs LLM@T3  [Addendum 33's actual comparison, but with attributes removed from the routine] | -7.8 (-10%) | +0.098 | -0.048 | SAME / SAME | NEITHER |
| T3-noattr vs routine@T2  [what access + map alone buy over attributes alone, on this world/sample] | -24.0 (-26%) | +0.049 | +0.000 | FASTER / SAME | IMPROVES |
| T3-noattr vs routine@T3  [what attributes still buy once access + map exist, on this world/sample] | +10.2 (+18%) | +0.016 | +0.000 | SLOWER / SAME | WORSE |

## By kind: routine@T3-noattr minus LLM@T3

| kind | d minutes | d accuracy | label |
|---|---|---|---|
| all | -7.8 (-10%) | +0.098 | NEITHER |
| single | +17.1 (+51%) | +0.100 | WORSE |
| multi | +27.2 (+25%) | +0.050 | WORSE |
| shared | -150.9 (-86%) | +0.167 | IMPROVES |

## Reading

T3-noattr sits between T2 and T3 by construction (T2's access, T3's map, neither's attributes). Read its row against both LLM pilots: beating LLM@T2 says the point map's speed carries even without attributes; the comparison against LLM@T3 is the one that matters most, since T3 is where the routine already won decisively in Addendum 33 -- this checks whether that margin survives losing attribute documentation. The by-kind table isolates whether any change is concentrated in shared-cause visits (the routine's own shortcut, unaffected by this item set) or elsewhere.

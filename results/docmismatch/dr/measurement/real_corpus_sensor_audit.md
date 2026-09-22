# Real building corpus: does the documentation already have the sensor `vav_zone` channels 0/2 need? (Addendum 5b)

46 real buildings (44 anonymized MORTAR + ORNL `rtu_exp`), offline from `data_cache/`, never the network. 30 have at least one VAV-class node. Per VAV box: does a `hasPoint` edge lead to a point whose Brick class is-a `Flow_Sensor` (present), confidently does not (absent), or is undetermined (a point exists under a Brick class the reference ontology cannot place -- never guessed)?

**Corpus-wide: 950 present / 1314 absent / 0 undetermined VAV boxes (17/30 buildings have at least one VAV box with the airflow point already documented).**

| building | n VAV | present | absent | undetermined |
|---|---|---|---|---|
| mortar_bldg1 | 8 | 8 | 0 | 0 |
| mortar_bldg10 | 16 | 0 | 16 | 0 |
| mortar_bldg11 | 394 | 93 | 301 | 0 |
| mortar_bldg12 | 98 | 72 | 26 | 0 |
| mortar_bldg13 | 24 | 12 | 12 | 0 |
| mortar_bldg15 | 129 | 102 | 27 | 0 |
| mortar_bldg18 | 144 | 0 | 144 | 0 |
| mortar_bldg2 | 25 | 0 | 25 | 0 |
| mortar_bldg20 | 13 | 0 | 13 | 0 |
| mortar_bldg22 | 2 | 1 | 1 | 0 |
| mortar_bldg25 | 2 | 0 | 2 | 0 |
| mortar_bldg27 | 17 | 17 | 0 | 0 |
| mortar_bldg28 | 45 | 0 | 45 | 0 |
| mortar_bldg30 | 99 | 99 | 0 | 0 |
| mortar_bldg32 | 107 | 0 | 107 | 0 |
| mortar_bldg34 | 39 | 14 | 25 | 0 |
| mortar_bldg36 | 43 | 0 | 43 | 0 |
| mortar_bldg37 | 283 | 237 | 46 | 0 |
| mortar_bldg39 | 18 | 0 | 18 | 0 |
| mortar_bldg4 | 28 | 12 | 16 | 0 |
| mortar_bldg40 | 87 | 69 | 18 | 0 |
| mortar_bldg42 | 13 | 13 | 0 | 0 |
| mortar_bldg43 | 52 | 0 | 52 | 0 |
| mortar_bldg44 | 44 | 16 | 28 | 0 |
| mortar_bldg5 | 124 | 0 | 124 | 0 |
| mortar_bldg6 | 151 | 0 | 151 | 0 |
| mortar_bldg8 | 24 | 24 | 0 | 0 |
| mortar_bldg9 | 126 | 62 | 64 | 0 |
| mortar_smc | 99 | 99 | 0 | 0 |
| rtu_exp | 10 | 0 | 10 | 0 |

(16 buildings have no VAV-class node at all -- `vav_zone` recommendations never apply to them.)

## Worked example

Building `rtu_exp`, VAV node `https://hvac-benchmark.invalid/building/rtu_exp/bldg-59#VAV_Box_102`:

> channel 0 of `vav_zone` is not BAS-only; it needs a temporary airflow (CFM) logger on the documented owner to be trustworthy on this building
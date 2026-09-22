# Continuous trust weight vs. binary exclusion (Addendum 8)

real DEV vav_zone episodes (n=1200), futility stopping on in all three variants (window=4, margin=0.05). Trust weights derived from real_channel_validity: `{0: 0.032796057421841995, 1: 0.06613171481393998, 2: 0.0}`.

## Technician reads

| variant | mean n_read | median n_read |
|---|---|---|
| no_adaptation | 8.0 | 8 |
| exclude_struct | 8.0 | 8 |
| trust_weighted | 8.0 | 8 |

## Forced accuracy

| variant (layer) | n eps | forced acc | diff vs exclude_struct |
|---|---|---|---|
| no_adaptation (none) | 1200 | 0.537 [0.502, 0.574] | -0.006 [-0.034, 0.023] |
| exclude_struct (none) | 1200 | 0.543 [0.514, 0.572] |  |
| trust_weighted (none) | 1200 | 0.504 [0.500, 0.509] | -0.039 [-0.066, -0.011] |
| no_adaptation (new) | 1200 | 0.537 [0.502, 0.574] | -0.006 [-0.034, 0.023] |
| exclude_struct (new) | 1200 | 0.543 [0.514, 0.572] |  |
| trust_weighted (new) | 1200 | 0.504 [0.500, 0.509] | -0.039 [-0.066, -0.011] |
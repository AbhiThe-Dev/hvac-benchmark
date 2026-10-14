# Correlated check errors: how much does the tool's independence assumption cost, and can it be repaired? (EXPLORATORY; written and hashed before any correlated run)

## The issue

The tool multiplies its checks' likelihoods as if, given the cause, each check's answer were independent. Several checks read the same underlying control-system data at one box (airflow, damper, hunting, zone temperature, reheat), so one bad data source can mislead them together. The simulations so far draw every answer independently, so they cannot show this; their confident-error numbers (6.8% at W0) are probably optimistic.

## The correlated world (my construction; no data say how often it happens)

Per (visit, room) a latent state "the control-system data for this box is invalid" (stale, frozen, wrong point mapped, wrong box) occurs with probability pi. When it does, ONE direction is drawn for the room (50/50) and EVERY control-system check at that box (checks with place "bas" and subject box or zone: `bas_airflow`, `bas_damper`, `bas_zone`, `bas_reheat`, `bas_hunting`) answers in that direction regardless of the cause:
"looks healthy" = abnormal with the check's own false-alarm rate; "looks faulty" = abnormal with probability 0.90. Everything else (air handler reads, at-the-box measurements, command-and-observe checks) is unchanged. pi in {0, 0.10, 0.25}; pi = 0 is the existing world.

## What the tool does about it (three arms; the engine file is not modified: a subclass of the session overrides the posterior)

- **independent** (today): every observation multiplies in.
- **tempered**: the room's control-system box observations (n of them) are combined with their log-likelihood scaled by 1/n, so the group counts as about one observation.
- **mixture**: the group's likelihood is (1 - p_t) x (product of the independent likelihoods) + p_t x (a cause-independent "data invalid" term: 0.5 x product under looks-healthy + 0.5 x product under looks-faulty), with p_t = 0.10 assumed (not the truth in every cell). With p_t = 0 it must equal the independent arm exactly.

## Visits, worlds, measures

The same 100 registered visits, the demo's mixed setting, `min_rate` 0.02, T3-noattr; W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5). Per cell: accuracy, wrong-and-confident, minutes per visit; accuracy and wrong-and-confident for the rooms whose data are invalid and the rooms whose data are valid; paired bootstrap over visits (2000) against the independent tool at pi = 0.

## Gates (a failed gate = NO RESULT)

G1: independent arm at pi = 0 equals the stored 74.83% / 54.67% and 193.7 / 204.8 minutes. G2: the mixture arm with p_t = 0 equals the independent arm exactly (guesses, conclusions, minutes) on every visit at pi = 0.10. G3: the oracle is order-independent (the same control-system questions asked forward and backward give identical answers on 20 visits).

## Decision rule (fixed now)

HARM of correlation: wrong-and-confident of the independent tool rises by at least 1 point from pi = 0 to pi = 0.10 with a paired 95% interval above 0. An arm REPAIRS if, at pi = 0.10, its wrong-and-confident is within 1 point of the pi = 0 independent-tool level, it loses at most 2 accuracy points against the independent tool at pi = 0.10, and adds at most 10% minutes. The W1 results are reported next to the W0 verdict.

## Predictions (before any correlated run)

- C1: at W0 and pi = 0.10 the independent tool's wrong-and-confident is at least 2 points higher than at pi = 0 (6.8%).
- C2: at pi = 0.25 the independent tool's accuracy is at least 3 points lower than at pi = 0.
- C3: the mixture arm at pi = 0.10 brings wrong-and-confident back within 1 point of the pi = 0 level.
- C4: the tempered arm lowers wrong-and-confident at pi = 0.10 against the independent tool, but by less than the mixture arm does.
- C5: at pi = 0 neither repair costs more than 2 accuracy points against the independent tool.
- C6: the mixture arm adds at least 5% to minutes per visit at pi = 0.10 (less certain belief asks more questions).

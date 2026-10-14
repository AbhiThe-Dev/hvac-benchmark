# Where does the joint tool's extra time go? (exploratory note E1)

Simulation only, the model's own family, placeholder numbers; not a pre-registered test; the variants (`joint2_focus`, `joint2_cap12`) were designed after looking at the diagnosis. Every policy gets the SAME answer to the same question (a coupled oracle), so differences between policies are the policies alone. The routine is `tool_ticket_memo2`, the joint tool `tool_joint2`; both are Addendum 31's, at the conclusion threshold tau shown (the tool's own is 0.95). `joint2_cap12`: the joint session with the routine's cap of 12 room or box checks per complaint. `joint2_focus`: the joint session working the complaints in arrival order.

Gate (the instrumented replays reproduce Addendum 31's stored minutes, checks and correct counts): **PASS**, 800 replays, 0 differ.

## Run `diagnose`: events 0-999 of the primary cell, answer seeds 201-208, policies tool_ticket_memo2, tool_joint2

**shared-cause visits, T2, tau 0.95** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 83.0 | 7.12 | 3.72 | 28.1 | 0.0 | 93.3 | 2.2 |
| tool_joint2 | 92.0 | 7.62 | 4.58 | 32.0 | 2.7 | 96.1 | 1.8 |

**shared-cause visits, T3, tau 0.95** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 36.4 | 6.99 | 3.29 | 7.9 | 0.0 | 94.3 | 3.7 |
| tool_joint2 | 55.9 | 8.94 | 4.10 | 15.0 | 10.5 | 96.3 | 2.6 |

**several complaints, no shared cause, T2, tau 0.95** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 190.6 | 19.65 | 7.43 | 44.4 | 0.0 | 75.3 | 1.3 |
| tool_joint2 | 210.0 | 19.83 | 10.33 | 56.9 | 14.7 | 76.9 | 0.8 |

**several complaints, no shared cause, T3, tau 0.95** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 112.9 | 21.88 | 8.07 | 17.2 | 0.0 | 78.6 | 1.3 |
| tool_joint2 | 134.8 | 23.63 | 8.89 | 24.4 | 23.2 | 83.1 | 1.3 |

**all visits, T2, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 111.2 | 11.10 | 4.47 | 27.3 | 0.0 | 79.4 | 1.6 |
| tool_joint2 | 117.7 | 11.23 | 5.36 | 31.1 | 4.2 | 80.3 | 1.3 |

**all visits, T3, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 63.4 | 12.21 | 4.69 | 10.1 | 0.0 | 82.3 | 2.2 |
| tool_joint2 | 72.4 | 12.99 | 5.04 | 13.1 | 7.7 | 83.8 | 1.7 |

### Paired differences in run `diagnose` (first minus second, per event over the answer seeds; 95% bootstrap interval over events)

| subset | tier | tau | tool_joint2 - tool_ticket_memo2 |
|---|---|---|---|
| shared-cause visits | T2 | 0.95 | +9.0 [+4.2, +14.4] min, +2.8 pts |
| shared-cause visits | T3 | 0.95 | +19.4 [+14.8, +24.6] min, +2.0 pts |
| several complaints, no shared cause | T2 | 0.95 | +19.4 [+16.6, +22.5] min, +1.5 pts |
| several complaints, no shared cause | T3 | 0.95 | +22.0 [+19.9, +24.1] min, +4.5 pts |
| all visits | T2 | 0.95 | +6.5 [+5.3, +7.8] min, +0.9 pts |
| all visits | T3 | 0.95 | +8.9 [+7.8, +10.2] min, +1.5 pts |

## Run `sweep`: events 0-999 of the primary cell, answer seeds 201-204, policies tool_ticket_memo2, tool_joint2

**shared-cause visits, T2, tau 0.90** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 73.8 | 6.43 | 3.31 | 24.2 | 0.0 | 93.4 | 3.0 |
| tool_joint2 | 74.6 | 6.32 | 3.61 | 26.4 | 2.4 | 95.2 | 2.7 |

**shared-cause visits, T2, tau 0.92** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 74.1 | 6.45 | 3.31 | 24.2 | 0.0 | 93.4 | 2.8 |
| tool_joint2 | 78.9 | 6.57 | 3.79 | 27.3 | 2.5 | 95.4 | 2.3 |

**shared-cause visits, T2, tau 0.94** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 75.8 | 6.70 | 3.35 | 24.5 | 0.0 | 93.4 | 2.7 |
| tool_joint2 | 87.6 | 7.22 | 4.30 | 30.4 | 2.6 | 95.3 | 2.1 |

**shared-cause visits, T2, tau 0.95** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 84.3 | 7.21 | 3.77 | 28.3 | 0.0 | 93.3 | 2.3 |
| tool_joint2 | 92.3 | 7.63 | 4.55 | 31.8 | 2.6 | 95.4 | 2.0 |

**shared-cause visits, T2, tau 0.97** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 85.1 | 7.31 | 3.87 | 28.4 | 0.0 | 93.3 | 2.0 |
| tool_joint2 | 141.4 | 11.92 | 7.76 | 50.5 | 4.7 | 95.8 | 0.8 |

**shared-cause visits, T2, tau 0.99** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 86.2 | 7.55 | 3.90 | 28.6 | 0.0 | 93.3 | 1.0 |
| tool_joint2 | 153.2 | 12.79 | 8.47 | 54.4 | 4.6 | 95.8 | 0.1 |

**shared-cause visits, T3, tau 0.90** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 32.8 | 6.52 | 3.10 | 7.1 | 0.0 | 94.4 | 3.7 |
| tool_joint2 | 38.8 | 7.00 | 3.03 | 7.9 | 8.9 | 95.4 | 4.0 |

**shared-cause visits, T3, tau 0.92** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 33.8 | 6.71 | 3.14 | 7.2 | 0.0 | 94.5 | 3.6 |
| tool_joint2 | 40.7 | 7.21 | 3.12 | 8.4 | 9.5 | 95.5 | 3.8 |

**shared-cause visits, T3, tau 0.94** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 35.0 | 6.88 | 3.20 | 7.5 | 0.0 | 94.5 | 3.5 |
| tool_joint2 | 47.2 | 7.91 | 3.54 | 11.1 | 10.0 | 95.8 | 3.3 |

**shared-cause visits, T3, tau 0.95** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 35.6 | 6.95 | 3.22 | 7.6 | 0.0 | 94.6 | 3.4 |
| tool_joint2 | 55.2 | 8.95 | 4.07 | 15.0 | 10.2 | 96.3 | 2.5 |

**shared-cause visits, T3, tau 0.97** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 48.6 | 8.41 | 4.22 | 13.1 | 0.0 | 94.9 | 1.9 |
| tool_joint2 | 80.4 | 14.24 | 5.78 | 21.1 | 14.5 | 97.3 | 1.3 |

**shared-cause visits, T3, tau 0.99** (172 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 52.8 | 9.44 | 4.58 | 14.5 | 0.0 | 95.0 | 1.5 |
| tool_joint2 | 125.7 | 19.49 | 9.61 | 38.7 | 15.3 | 97.9 | 0.1 |

**several complaints, no shared cause, T2, tau 0.90** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 177.2 | 18.57 | 6.91 | 41.5 | 0.0 | 75.4 | 3.2 |
| tool_joint2 | 200.1 | 19.11 | 9.78 | 54.1 | 14.8 | 76.9 | 2.6 |

**several complaints, no shared cause, T2, tau 0.92** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 179.4 | 18.77 | 6.92 | 41.5 | 0.0 | 75.4 | 3.0 |
| tool_joint2 | 201.7 | 19.22 | 9.81 | 54.3 | 14.9 | 76.9 | 2.3 |

**several complaints, no shared cause, T2, tau 0.94** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 182.3 | 19.08 | 6.97 | 41.8 | 0.0 | 75.4 | 2.1 |
| tool_joint2 | 202.8 | 19.31 | 9.87 | 54.6 | 14.9 | 76.9 | 1.3 |

**several complaints, no shared cause, T2, tau 0.95** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 188.6 | 19.53 | 7.37 | 44.0 | 0.0 | 75.4 | 1.3 |
| tool_joint2 | 208.7 | 19.75 | 10.31 | 56.8 | 14.8 | 76.9 | 0.6 |

**several complaints, no shared cause, T2, tau 0.97** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 191.4 | 19.89 | 7.72 | 44.1 | 0.0 | 75.4 | 0.6 |
| tool_joint2 | 211.4 | 20.10 | 10.67 | 57.0 | 14.8 | 76.9 | 0.1 |

**several complaints, no shared cause, T2, tau 0.99** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 191.6 | 19.91 | 7.73 | 44.2 | 0.0 | 75.4 | 0.0 |
| tool_joint2 | 211.2 | 20.08 | 10.66 | 56.9 | 14.8 | 76.9 | 0.0 |

**several complaints, no shared cause, T3, tau 0.90** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 101.7 | 20.46 | 7.58 | 16.0 | 0.0 | 78.8 | 3.5 |
| tool_joint2 | 124.9 | 22.43 | 8.10 | 22.1 | 23.3 | 83.2 | 3.6 |

**several complaints, no shared cause, T3, tau 0.92** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 104.8 | 20.84 | 7.72 | 16.5 | 0.0 | 78.9 | 2.7 |
| tool_joint2 | 128.4 | 22.83 | 8.31 | 23.0 | 23.5 | 83.3 | 2.9 |

**several complaints, no shared cause, T3, tau 0.94** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 109.9 | 21.55 | 7.89 | 16.8 | 0.0 | 79.1 | 1.5 |
| tool_joint2 | 133.3 | 23.42 | 8.66 | 24.0 | 23.8 | 83.6 | 1.5 |

**several complaints, no shared cause, T3, tau 0.95** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 113.3 | 21.93 | 8.04 | 17.3 | 0.0 | 79.0 | 1.3 |
| tool_joint2 | 135.8 | 23.71 | 8.87 | 24.7 | 23.6 | 83.7 | 1.2 |

**several complaints, no shared cause, T3, tau 0.97** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 114.5 | 22.14 | 8.11 | 17.4 | 0.0 | 79.1 | 0.6 |
| tool_joint2 | 138.0 | 24.04 | 9.07 | 25.1 | 23.6 | 83.8 | 0.5 |

**several complaints, no shared cause, T3, tau 0.99** (255 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 114.8 | 22.21 | 8.14 | 17.4 | 0.0 | 79.1 | 0.3 |
| tool_joint2 | 138.1 | 24.07 | 9.09 | 25.2 | 23.6 | 83.8 | 0.2 |

**all visits, T2, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 103.0 | 10.45 | 4.12 | 24.9 | 0.0 | 79.4 | 2.9 |
| tool_joint2 | 109.0 | 10.57 | 4.90 | 28.5 | 4.2 | 80.1 | 2.6 |

**all visits, T2, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 104.1 | 10.55 | 4.13 | 25.0 | 0.0 | 79.5 | 2.7 |
| tool_joint2 | 110.6 | 10.69 | 4.95 | 28.8 | 4.2 | 80.2 | 2.3 |

**all visits, T2, tau 0.94** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 105.8 | 10.74 | 4.15 | 25.1 | 0.0 | 79.5 | 2.3 |
| tool_joint2 | 113.0 | 10.89 | 5.06 | 29.4 | 4.2 | 80.2 | 1.8 |

**all visits, T2, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 110.7 | 11.07 | 4.45 | 27.1 | 0.0 | 79.5 | 1.7 |
| tool_joint2 | 117.2 | 11.20 | 5.33 | 30.9 | 4.2 | 80.2 | 1.4 |

**all visits, T2, tau 0.97** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 112.3 | 11.29 | 4.66 | 27.1 | 0.0 | 79.5 | 1.1 |
| tool_joint2 | 127.1 | 12.14 | 6.08 | 34.2 | 4.6 | 80.3 | 0.5 |

**all visits, T2, tau 0.99** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 112.6 | 11.34 | 4.67 | 27.2 | 0.0 | 79.5 | 0.5 |
| tool_joint2 | 129.1 | 12.28 | 6.20 | 34.9 | 4.6 | 80.3 | 0.1 |

**all visits, T3, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 57.5 | 11.46 | 4.43 | 9.4 | 0.0 | 82.1 | 3.4 |
| tool_joint2 | 64.5 | 12.04 | 4.56 | 11.1 | 7.5 | 83.4 | 3.5 |

**all visits, T3, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 59.3 | 11.69 | 4.51 | 9.7 | 0.0 | 82.3 | 2.9 |
| tool_joint2 | 66.6 | 12.28 | 4.66 | 11.5 | 7.6 | 83.6 | 3.0 |

**all visits, T3, tau 0.94** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 61.8 | 12.02 | 4.60 | 9.8 | 0.0 | 82.4 | 2.3 |
| tool_joint2 | 69.9 | 12.68 | 4.86 | 12.3 | 7.8 | 83.8 | 2.2 |

**all visits, T3, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 63.5 | 12.23 | 4.67 | 10.0 | 0.0 | 82.4 | 2.0 |
| tool_joint2 | 72.6 | 13.03 | 5.03 | 13.2 | 7.8 | 83.9 | 1.6 |

**all visits, T3, tau 0.97** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 66.4 | 12.59 | 4.88 | 11.0 | 0.0 | 82.5 | 1.1 |
| tool_joint2 | 77.8 | 14.08 | 5.40 | 14.4 | 8.5 | 84.1 | 0.8 |

**all visits, T3, tau 0.99** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 67.2 | 12.79 | 4.96 | 11.3 | 0.0 | 82.5 | 0.8 |
| tool_joint2 | 85.7 | 15.00 | 6.07 | 17.4 | 8.6 | 84.2 | 0.1 |

### Paired differences in run `sweep` (first minus second, per event over the answer seeds; 95% bootstrap interval over events)

| subset | tier | tau | tool_joint2 - tool_ticket_memo2 |
|---|---|---|---|
| shared-cause visits | T2 | 0.90 | +0.8 [-4.5, +5.5] min, +1.8 pts |
| shared-cause visits | T2 | 0.92 | +4.7 [-0.6, +9.4] min, +1.9 pts |
| shared-cause visits | T2 | 0.94 | +11.8 [+6.3, +16.9] min, +1.9 pts |
| shared-cause visits | T2 | 0.95 | +7.9 [+2.8, +13.7] min, +2.1 pts |
| shared-cause visits | T2 | 0.96 | +15.1 [+9.4, +21.0] min, +2.1 pts |
| shared-cause visits | T2 | 0.97 | +56.4 [+47.5, +66.0] min, +2.5 pts |
| shared-cause visits | T2 | 0.98 | +63.0 [+53.5, +72.7] min, +2.3 pts |
| shared-cause visits | T2 | 0.99 | +67.0 [+57.8, +76.9] min, +2.5 pts |
| shared-cause visits | T3 | 0.90 | +6.0 [+2.4, +9.6] min, +0.9 pts |
| shared-cause visits | T3 | 0.92 | +7.0 [+3.3, +10.7] min, +1.0 pts |
| shared-cause visits | T3 | 0.94 | +12.2 [+8.1, +16.4] min, +1.3 pts |
| shared-cause visits | T3 | 0.95 | +19.6 [+15.0, +24.6] min, +1.7 pts |
| shared-cause visits | T3 | 0.96 | +10.4 [+6.1, +14.8] min, +1.7 pts |
| shared-cause visits | T3 | 0.97 | +31.8 [+25.7, +38.9] min, +2.4 pts |
| shared-cause visits | T3 | 0.98 | +45.7 [+38.3, +53.6] min, +2.6 pts |
| shared-cause visits | T3 | 0.99 | +72.9 [+63.5, +82.1] min, +2.9 pts |
| several complaints, no shared cause | T2 | 0.90 | +22.9 [+19.6, +26.5] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.92 | +22.3 [+18.9, +26.0] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.94 | +20.4 [+17.0, +24.0] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.95 | +20.1 [+16.7, +23.6] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.96 | +20.0 [+16.6, +23.5] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.97 | +19.9 [+16.6, +23.4] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.98 | +19.9 [+16.6, +23.4] min, +1.5 pts |
| several complaints, no shared cause | T2 | 0.99 | +19.6 [+16.3, +23.1] min, +1.5 pts |
| several complaints, no shared cause | T3 | 0.90 | +23.2 [+20.5, +25.9] min, +4.3 pts |
| several complaints, no shared cause | T3 | 0.92 | +23.6 [+21.0, +26.2] min, +4.3 pts |
| several complaints, no shared cause | T3 | 0.94 | +23.4 [+20.9, +26.0] min, +4.4 pts |
| several complaints, no shared cause | T3 | 0.95 | +22.5 [+20.1, +25.1] min, +4.6 pts |
| several complaints, no shared cause | T3 | 0.96 | +23.3 [+21.0, +25.9] min, +4.6 pts |
| several complaints, no shared cause | T3 | 0.97 | +23.5 [+21.2, +26.0] min, +4.7 pts |
| several complaints, no shared cause | T3 | 0.98 | +23.4 [+21.1, +25.9] min, +4.7 pts |
| several complaints, no shared cause | T3 | 0.99 | +23.4 [+21.0, +25.9] min, +4.7 pts |
| all visits | T2 | 0.90 | +6.0 [+4.6, +7.4] min, +0.7 pts |
| all visits | T2 | 0.92 | +6.5 [+5.2, +7.9] min, +0.7 pts |
| all visits | T2 | 0.94 | +7.2 [+5.9, +8.7] min, +0.7 pts |
| all visits | T2 | 0.95 | +6.5 [+5.1, +7.9] min, +0.7 pts |
| all visits | T2 | 0.96 | +7.7 [+6.3, +9.2] min, +0.7 pts |
| all visits | T2 | 0.97 | +14.8 [+12.6, +17.2] min, +0.8 pts |
| all visits | T2 | 0.98 | +15.9 [+13.6, +18.4] min, +0.8 pts |
| all visits | T2 | 0.99 | +16.5 [+14.2, +19.0] min, +0.8 pts |
| all visits | T3 | 0.90 | +6.9 [+5.9, +8.1] min, +1.3 pts |
| all visits | T3 | 0.92 | +7.2 [+6.2, +8.3] min, +1.3 pts |
| all visits | T3 | 0.94 | +8.1 [+7.0, +9.2] min, +1.3 pts |
| all visits | T3 | 0.95 | +9.1 [+7.9, +10.3] min, +1.5 pts |
| all visits | T3 | 0.96 | +7.7 [+6.6, +8.9] min, +1.5 pts |
| all visits | T3 | 0.97 | +11.5 [+9.9, +13.0] min, +1.6 pts |
| all visits | T3 | 0.98 | +13.8 [+12.0, +15.7] min, +1.6 pts |
| all visits | T3 | 0.99 | +18.5 [+16.0, +21.0] min, +1.7 pts |

## Run `focus`: events 1000-1999 of the primary cell, answer seeds 301-304, policies tool_ticket_memo2, tool_joint2, joint2_focus

**shared-cause visits, T2, tau 0.90** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 88.7 | 8.02 | 4.10 | 29.7 | 0.0 | 92.6 | 3.6 |
| tool_joint2 | 95.1 | 8.00 | 4.64 | 33.0 | 6.5 | 95.3 | 2.8 |
| joint2_focus | 99.8 | 8.33 | 4.19 | 32.2 | 7.0 | 95.5 | 2.5 |

**shared-cause visits, T2, tau 0.92** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 89.2 | 8.06 | 4.11 | 29.8 | 0.0 | 92.6 | 3.3 |
| tool_joint2 | 98.5 | 8.22 | 4.81 | 33.9 | 6.5 | 95.3 | 2.8 |
| joint2_focus | 103.6 | 8.60 | 4.37 | 33.1 | 7.0 | 95.8 | 2.2 |

**shared-cause visits, T2, tau 0.95** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 102.7 | 8.99 | 4.70 | 34.4 | 0.0 | 93.4 | 1.6 |
| tool_joint2 | 114.9 | 9.44 | 5.73 | 39.2 | 7.0 | 95.8 | 2.1 |
| joint2_focus | 123.0 | 9.99 | 5.17 | 37.7 | 7.1 | 95.9 | 1.9 |

**shared-cause visits, T3, tau 0.90** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 44.7 | 8.50 | 4.07 | 10.6 | 0.0 | 94.6 | 2.5 |
| tool_joint2 | 53.5 | 9.06 | 3.91 | 11.9 | 12.9 | 96.5 | 2.8 |
| joint2_focus | 53.8 | 8.70 | 4.11 | 12.1 | 12.8 | 96.3 | 2.9 |

**shared-cause visits, T3, tau 0.92** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 46.1 | 8.75 | 4.14 | 10.8 | 0.0 | 94.6 | 2.4 |
| tool_joint2 | 56.4 | 9.39 | 4.08 | 12.7 | 13.5 | 96.5 | 2.7 |
| joint2_focus | 57.4 | 9.11 | 4.32 | 12.9 | 13.5 | 96.2 | 2.9 |

**shared-cause visits, T3, tau 0.95** (152 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 49.4 | 9.15 | 4.28 | 11.4 | 0.0 | 94.5 | 2.1 |
| tool_joint2 | 73.9 | 11.19 | 5.10 | 19.4 | 15.0 | 96.9 | 2.0 |
| joint2_focus | 76.4 | 10.80 | 5.61 | 19.7 | 14.9 | 96.8 | 1.9 |

**several complaints, no shared cause, T2, tau 0.90** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 179.3 | 18.48 | 6.98 | 42.1 | 0.0 | 75.9 | 2.9 |
| tool_joint2 | 201.9 | 19.08 | 9.70 | 54.2 | 15.5 | 76.8 | 2.7 |
| joint2_focus | 197.2 | 19.31 | 7.50 | 46.1 | 19.2 | 76.8 | 2.7 |

**several complaints, no shared cause, T2, tau 0.92** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 182.1 | 18.71 | 7.00 | 42.2 | 0.0 | 75.9 | 2.6 |
| tool_joint2 | 203.6 | 19.19 | 9.75 | 54.4 | 15.6 | 76.8 | 2.3 |
| joint2_focus | 200.0 | 19.55 | 7.53 | 46.2 | 19.2 | 76.8 | 2.4 |

**several complaints, no shared cause, T2, tau 0.95** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 191.0 | 19.42 | 7.45 | 44.7 | 0.0 | 76.0 | 1.1 |
| tool_joint2 | 210.4 | 19.68 | 10.23 | 57.0 | 15.6 | 76.8 | 1.0 |
| joint2_focus | 209.2 | 20.28 | 7.97 | 48.8 | 19.5 | 76.9 | 1.1 |

**several complaints, no shared cause, T3, tau 0.90** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 99.9 | 20.13 | 7.42 | 15.5 | 0.0 | 77.5 | 3.2 |
| tool_joint2 | 123.7 | 21.98 | 8.08 | 22.1 | 24.0 | 82.9 | 4.2 |
| joint2_focus | 130.7 | 22.19 | 8.72 | 22.9 | 37.9 | 80.5 | 3.7 |

**several complaints, no shared cause, T3, tau 0.92** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 102.9 | 20.52 | 7.55 | 16.0 | 0.0 | 77.6 | 2.4 |
| tool_joint2 | 127.6 | 22.44 | 8.30 | 23.0 | 24.6 | 83.1 | 3.3 |
| joint2_focus | 133.8 | 22.60 | 8.87 | 23.4 | 38.6 | 80.2 | 3.0 |

**several complaints, no shared cause, T3, tau 0.95** (250 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 110.3 | 21.45 | 7.82 | 16.6 | 0.0 | 77.6 | 1.3 |
| tool_joint2 | 134.2 | 23.22 | 8.75 | 24.2 | 24.9 | 83.2 | 2.1 |
| joint2_focus | 140.9 | 23.48 | 9.17 | 24.0 | 39.9 | 79.6 | 1.7 |

**all visits, T2, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 105.3 | 10.72 | 4.21 | 25.5 | 0.0 | 78.1 | 3.1 |
| tool_joint2 | 111.9 | 10.87 | 4.97 | 29.1 | 4.9 | 78.8 | 2.8 |
| joint2_focus | 111.5 | 10.98 | 4.35 | 26.9 | 5.9 | 78.8 | 2.6 |

**all visits, T2, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 106.6 | 10.83 | 4.22 | 25.6 | 0.0 | 78.1 | 2.9 |
| tool_joint2 | 113.4 | 10.97 | 5.01 | 29.3 | 4.9 | 78.8 | 2.6 |
| joint2_focus | 113.3 | 11.12 | 4.39 | 27.1 | 5.9 | 78.9 | 2.3 |

**all visits, T2, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 113.3 | 11.34 | 4.55 | 27.6 | 0.0 | 78.3 | 1.3 |
| tool_joint2 | 120.0 | 11.47 | 5.40 | 31.4 | 5.0 | 78.9 | 1.5 |
| joint2_focus | 120.9 | 11.70 | 4.75 | 29.1 | 5.9 | 78.9 | 1.4 |

**all visits, T3, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 58.1 | 11.63 | 4.47 | 9.5 | 0.0 | 81.0 | 2.9 |
| tool_joint2 | 65.4 | 12.18 | 4.61 | 11.3 | 8.0 | 82.6 | 3.3 |
| joint2_focus | 67.2 | 12.17 | 4.80 | 11.6 | 11.4 | 82.0 | 3.3 |

**all visits, T3, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 60.0 | 11.87 | 4.55 | 9.8 | 0.0 | 81.0 | 2.4 |
| tool_joint2 | 67.7 | 12.45 | 4.73 | 11.8 | 8.2 | 82.7 | 2.8 |
| joint2_focus | 69.5 | 12.45 | 4.91 | 11.9 | 11.7 | 81.9 | 2.8 |

**all visits, T3, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 64.4 | 12.43 | 4.73 | 10.2 | 0.0 | 81.2 | 1.5 |
| tool_joint2 | 74.1 | 13.18 | 5.08 | 13.3 | 8.5 | 82.9 | 1.6 |
| joint2_focus | 76.2 | 13.19 | 5.27 | 13.3 | 12.2 | 82.0 | 1.5 |

### Paired differences in run `focus` (first minus second, per event over the answer seeds; 95% bootstrap interval over events)

| subset | tier | tau | tool_joint2 - tool_ticket_memo2 | joint2_focus - tool_ticket_memo2 | joint2_focus - tool_joint2 |
|---|---|---|---|---|---|
| shared-cause visits | T2 | 0.90 | +6.4 [-1.0, +14.3] min, +2.7 pts | +11.0 [+4.8, +18.5] min, +2.9 pts | +4.7 [+0.9, +8.8] min, +0.2 pts |
| shared-cause visits | T2 | 0.92 | +9.3 [+2.4, +17.0] min, +2.7 pts | +14.5 [+8.2, +22.0] min, +3.2 pts | +5.1 [+1.4, +9.4] min, +0.5 pts |
| shared-cause visits | T2 | 0.95 | +12.2 [+6.1, +18.6] min, +2.4 pts | +20.3 [+13.6, +27.5] min, +2.5 pts | +8.1 [+3.8, +12.8] min, +0.1 pts |
| shared-cause visits | T3 | 0.90 | +8.8 [+3.4, +14.3] min, +1.9 pts | +9.2 [+4.4, +13.9] min, +1.7 pts | +0.3 [-2.7, +3.5] min, -0.2 pts |
| shared-cause visits | T3 | 0.92 | +10.3 [+5.1, +15.6] min, +1.9 pts | +11.3 [+6.4, +16.1] min, +1.6 pts | +1.0 [-2.1, +4.0] min, -0.3 pts |
| shared-cause visits | T3 | 0.95 | +24.6 [+18.5, +31.0] min, +2.4 pts | +27.1 [+20.8, +33.8] min, +2.3 pts | +2.5 [-1.0, +6.2] min, -0.1 pts |
| several complaints, no shared cause | T2 | 0.90 | +22.6 [+19.0, +26.6] min, +0.9 pts | +17.9 [+14.3, +21.6] min, +0.9 pts | -4.7 [-6.9, -2.6] min, -0.1 pts |
| several complaints, no shared cause | T2 | 0.92 | +21.5 [+18.0, +25.6] min, +0.9 pts | +17.9 [+14.4, +21.7] min, +0.9 pts | -3.6 [-5.8, -1.4] min, -0.0 pts |
| several complaints, no shared cause | T2 | 0.95 | +19.4 [+15.8, +23.6] min, +0.9 pts | +18.2 [+14.6, +22.2] min, +0.9 pts | -1.2 [-3.4, +1.1] min, +0.1 pts |
| several complaints, no shared cause | T3 | 0.90 | +23.8 [+20.4, +27.9] min, +5.4 pts | +30.9 [+26.7, +35.6] min, +3.0 pts | +7.1 [+5.1, +9.3] min, -2.4 pts |
| several complaints, no shared cause | T3 | 0.92 | +24.6 [+21.2, +28.8] min, +5.6 pts | +30.9 [+26.7, +35.6] min, +2.6 pts | +6.2 [+4.1, +8.5] min, -3.0 pts |
| several complaints, no shared cause | T3 | 0.95 | +23.9 [+20.6, +27.9] min, +5.5 pts | +30.6 [+26.7, +34.9] min, +2.0 pts | +6.6 [+4.4, +8.9] min, -3.5 pts |
| all visits | T2 | 0.90 | +6.6 [+5.1, +8.2] min, +0.6 pts | +6.1 [+4.8, +7.6] min, +0.7 pts | -0.5 [-1.3, +0.4] min, +0.0 pts |
| all visits | T2 | 0.92 | +6.8 [+5.2, +8.4] min, +0.6 pts | +6.7 [+5.3, +8.2] min, +0.7 pts | -0.1 [-1.0, +0.7] min, +0.1 pts |
| all visits | T2 | 0.95 | +6.7 [+5.3, +8.1] min, +0.6 pts | +7.6 [+6.1, +9.2] min, +0.6 pts | +0.9 [+0.0, +1.9] min, +0.0 pts |
| all visits | T3 | 0.90 | +7.3 [+5.9, +8.7] min, +1.6 pts | +9.1 [+7.6, +10.6] min, +1.0 pts | +1.8 [+1.1, +2.5] min, -0.6 pts |
| all visits | T3 | 0.92 | +7.7 [+6.4, +9.1] min, +1.7 pts | +9.4 [+7.9, +11.0] min, +0.9 pts | +1.7 [+1.0, +2.5] min, -0.8 pts |
| all visits | T3 | 0.95 | +9.7 [+8.2, +11.2] min, +1.7 pts | +11.8 [+10.1, +13.4] min, +0.8 pts | +2.0 [+1.3, +2.9] min, -0.9 pts |

## Run `cap`: events 2000-2999 of the primary cell, answer seeds 401-404, policies tool_ticket_memo2, tool_joint2, joint2_cap12

**shared-cause visits, T2, tau 0.90** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 80.7 | 7.21 | 3.67 | 26.8 | 0.0 | 93.6 | 1.9 |
| tool_joint2 | 80.7 | 6.85 | 4.00 | 28.9 | 4.3 | 95.1 | 2.9 |
| joint2_cap12 | 76.4 | 6.59 | 3.90 | 28.2 | 0.0 | 94.9 | 2.9 |

**shared-cause visits, T2, tau 0.92** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 81.7 | 7.30 | 3.69 | 26.9 | 0.0 | 93.5 | 1.6 |
| tool_joint2 | 85.4 | 7.18 | 4.24 | 30.1 | 4.3 | 95.3 | 2.5 |
| joint2_cap12 | 81.2 | 6.91 | 4.14 | 29.5 | 0.0 | 95.1 | 2.5 |

**shared-cause visits, T2, tau 0.94** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 83.1 | 7.51 | 3.73 | 27.1 | 0.0 | 93.5 | 1.5 |
| tool_joint2 | 94.1 | 7.83 | 4.76 | 33.2 | 4.3 | 95.6 | 2.0 |
| joint2_cap12 | 89.8 | 7.57 | 4.66 | 32.6 | 0.0 | 95.4 | 2.0 |

**shared-cause visits, T2, tau 0.95** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 91.5 | 8.02 | 4.16 | 31.1 | 0.0 | 93.1 | 1.4 |
| tool_joint2 | 100.3 | 8.33 | 5.11 | 35.3 | 4.3 | 95.6 | 1.9 |
| joint2_cap12 | 96.0 | 8.07 | 5.01 | 34.6 | 0.0 | 95.4 | 1.9 |

**shared-cause visits, T3, tau 0.90** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 36.0 | 6.94 | 3.38 | 8.1 | 0.0 | 94.3 | 3.3 |
| tool_joint2 | 42.9 | 7.51 | 3.31 | 9.0 | 10.1 | 95.4 | 3.5 |
| joint2_cap12 | 33.0 | 6.69 | 2.92 | 7.2 | 0.0 | 95.0 | 3.5 |

**shared-cause visits, T3, tau 0.92** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 37.3 | 7.19 | 3.43 | 8.3 | 0.0 | 94.3 | 3.2 |
| tool_joint2 | 45.1 | 7.76 | 3.44 | 9.7 | 10.5 | 95.5 | 3.4 |
| joint2_cap12 | 34.7 | 6.89 | 3.04 | 7.8 | 0.0 | 95.1 | 3.4 |

**shared-cause visits, T3, tau 0.94** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 39.3 | 7.45 | 3.55 | 8.8 | 0.0 | 94.4 | 3.1 |
| tool_joint2 | 53.7 | 8.57 | 3.94 | 13.0 | 11.3 | 96.4 | 2.3 |
| joint2_cap12 | 42.6 | 7.67 | 3.51 | 11.0 | 0.0 | 96.0 | 2.3 |

**shared-cause visits, T3, tau 0.95** (151 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 40.1 | 7.56 | 3.58 | 8.8 | 0.0 | 94.4 | 3.0 |
| tool_joint2 | 61.9 | 9.56 | 4.46 | 16.2 | 11.5 | 96.5 | 2.1 |
| joint2_cap12 | 50.7 | 8.63 | 4.03 | 14.2 | 0.0 | 96.1 | 2.1 |

**several complaints, no shared cause, T2, tau 0.90** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 176.4 | 18.34 | 6.91 | 41.1 | 0.0 | 75.7 | 2.7 |
| tool_joint2 | 196.5 | 18.66 | 9.56 | 53.1 | 14.2 | 76.3 | 2.7 |
| joint2_cap12 | 185.3 | 17.97 | 9.29 | 51.1 | 0.0 | 74.7 | 2.7 |

**several complaints, no shared cause, T2, tau 0.92** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 178.1 | 18.49 | 6.92 | 41.2 | 0.0 | 75.7 | 2.5 |
| tool_joint2 | 198.0 | 18.76 | 9.62 | 53.5 | 14.5 | 76.3 | 2.4 |
| joint2_cap12 | 186.8 | 18.07 | 9.33 | 51.5 | 0.0 | 74.7 | 2.3 |

**several complaints, no shared cause, T2, tau 0.94** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 181.0 | 18.79 | 6.97 | 41.5 | 0.0 | 75.7 | 2.0 |
| tool_joint2 | 198.9 | 18.85 | 9.66 | 53.7 | 14.4 | 76.3 | 1.8 |
| joint2_cap12 | 187.8 | 18.16 | 9.38 | 51.7 | 0.0 | 74.7 | 1.8 |

**several complaints, no shared cause, T2, tau 0.95** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 188.5 | 19.32 | 7.46 | 44.3 | 0.0 | 75.7 | 1.2 |
| tool_joint2 | 206.5 | 19.38 | 10.19 | 56.6 | 14.6 | 76.4 | 1.2 |
| joint2_cap12 | 195.2 | 18.70 | 9.89 | 54.5 | 0.0 | 74.7 | 1.2 |

**several complaints, no shared cause, T3, tau 0.90** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 99.3 | 19.97 | 7.41 | 16.0 | 0.0 | 78.6 | 2.9 |
| tool_joint2 | 123.7 | 21.95 | 8.03 | 22.7 | 24.3 | 83.4 | 3.1 |
| joint2_cap12 | 102.7 | 20.21 | 7.19 | 18.5 | 0.0 | 79.1 | 2.9 |

**several complaints, no shared cause, T3, tau 0.92** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 101.9 | 20.30 | 7.53 | 16.4 | 0.0 | 78.7 | 2.5 |
| tool_joint2 | 127.0 | 22.31 | 8.23 | 23.5 | 24.5 | 83.5 | 2.7 |
| joint2_cap12 | 106.3 | 20.61 | 7.41 | 19.4 | 0.0 | 79.2 | 2.5 |

**several complaints, no shared cause, T3, tau 0.94** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 106.7 | 20.97 | 7.66 | 16.6 | 0.0 | 79.0 | 1.3 |
| tool_joint2 | 131.9 | 22.86 | 8.54 | 24.2 | 25.4 | 83.9 | 1.6 |
| joint2_cap12 | 111.1 | 21.20 | 7.73 | 20.0 | 0.0 | 79.5 | 1.4 |

**several complaints, no shared cause, T3, tau 0.95** (278 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 110.3 | 21.40 | 7.85 | 17.2 | 0.0 | 79.2 | 0.9 |
| tool_joint2 | 134.2 | 23.14 | 8.73 | 24.8 | 25.3 | 84.1 | 1.2 |
| joint2_cap12 | 114.3 | 21.55 | 7.96 | 20.8 | 0.0 | 79.7 | 1.2 |

**all visits, T2, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 106.6 | 10.86 | 4.26 | 25.8 | 0.0 | 77.6 | 2.4 |
| tool_joint2 | 112.2 | 10.89 | 5.05 | 29.4 | 4.6 | 77.9 | 2.8 |
| joint2_cap12 | 108.4 | 10.66 | 4.96 | 28.8 | 0.0 | 77.5 | 2.8 |

**all visits, T2, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 107.6 | 10.95 | 4.27 | 25.8 | 0.0 | 77.6 | 2.2 |
| tool_joint2 | 113.7 | 11.01 | 5.10 | 29.7 | 4.7 | 78.0 | 2.5 |
| joint2_cap12 | 110.0 | 10.77 | 5.01 | 29.0 | 0.0 | 77.5 | 2.5 |

**all visits, T2, tau 0.94** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 109.3 | 11.14 | 4.30 | 26.0 | 0.0 | 77.6 | 1.8 |
| tool_joint2 | 116.0 | 11.20 | 5.21 | 30.3 | 4.7 | 78.1 | 1.9 |
| joint2_cap12 | 112.2 | 10.97 | 5.11 | 29.6 | 0.0 | 77.6 | 1.9 |

**all visits, T2, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 114.4 | 11.48 | 4.61 | 27.9 | 0.0 | 77.6 | 1.2 |
| tool_joint2 | 120.7 | 11.55 | 5.52 | 32.0 | 4.7 | 78.2 | 1.5 |
| joint2_cap12 | 116.9 | 11.31 | 5.42 | 31.3 | 0.0 | 77.7 | 1.4 |

**all visits, T3, tau 0.90** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 59.0 | 11.75 | 4.53 | 9.7 | 0.0 | 80.8 | 3.3 |
| tool_joint2 | 66.8 | 12.38 | 4.69 | 11.7 | 8.3 | 82.4 | 3.4 |
| joint2_cap12 | 59.4 | 11.78 | 4.40 | 10.2 | 0.0 | 81.1 | 3.4 |

**all visits, T3, tau 0.92** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 60.8 | 11.98 | 4.60 | 10.0 | 0.0 | 81.0 | 2.9 |
| tool_joint2 | 68.9 | 12.63 | 4.79 | 12.2 | 8.4 | 82.5 | 3.0 |
| joint2_cap12 | 61.6 | 12.03 | 4.51 | 10.7 | 0.0 | 81.3 | 2.9 |

**all visits, T3, tau 0.94** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 63.5 | 12.35 | 4.70 | 10.2 | 0.0 | 81.4 | 2.1 |
| tool_joint2 | 72.7 | 13.05 | 5.00 | 12.9 | 8.8 | 83.0 | 1.9 |
| joint2_cap12 | 65.2 | 12.45 | 4.71 | 11.4 | 0.0 | 81.7 | 1.9 |

**all visits, T3, tau 0.95** (1000 events)

| policy | minutes | checks | moves | travel min | min beyond 12th check | % correct | % wrong-and-confident |
|---|---|---|---|---|---|---|---|
| tool_ticket_memo2 | 65.5 | 12.61 | 4.80 | 10.5 | 0.0 | 81.4 | 1.7 |
| tool_joint2 | 75.5 | 13.39 | 5.18 | 13.7 | 8.8 | 83.1 | 1.5 |
| joint2_cap12 | 68.2 | 12.81 | 4.90 | 12.2 | 0.0 | 81.8 | 1.5 |

### Paired differences in run `cap` (first minus second, per event over the answer seeds; 95% bootstrap interval over events)

| subset | tier | tau | tool_joint2 - tool_ticket_memo2 | joint2_cap12 - tool_ticket_memo2 | joint2_cap12 - tool_joint2 |
|---|---|---|---|---|---|
| shared-cause visits | T2 | 0.90 | +0.0 [-6.7, +6.4] min, +1.5 pts | -4.3 [-10.6, +1.5] min, +1.3 pts | -4.3 [-6.1, -2.7] min, -0.2 pts |
| shared-cause visits | T2 | 0.92 | +3.7 [-2.8, +10.2] min, +1.8 pts | -0.5 [-6.4, +5.2] min, +1.6 pts | -4.3 [-6.1, -2.7] min, -0.2 pts |
| shared-cause visits | T2 | 0.94 | +11.0 [+4.7, +17.3] min, +2.1 pts | +6.7 [+0.9, +12.3] min, +1.9 pts | -4.3 [-6.1, -2.7] min, -0.2 pts |
| shared-cause visits | T2 | 0.95 | +8.8 [+1.8, +15.6] min, +2.6 pts | +4.5 [-1.9, +10.7] min, +2.4 pts | -4.3 [-6.1, -2.7] min, -0.2 pts |
| shared-cause visits | T3 | 0.90 | +6.9 [+1.9, +11.6] min, +1.1 pts | -3.0 [-6.4, -0.1] min, +0.7 pts | -9.9 [-12.9, -6.8] min, -0.4 pts |
| shared-cause visits | T3 | 0.92 | +7.8 [+2.8, +12.4] min, +1.2 pts | -2.6 [-5.9, +0.3] min, +0.8 pts | -10.3 [-13.4, -7.3] min, -0.4 pts |
| shared-cause visits | T3 | 0.94 | +14.4 [+8.4, +20.1] min, +1.9 pts | +3.3 [-1.2, +7.9] min, +1.5 pts | -11.1 [-14.1, -8.0] min, -0.4 pts |
| shared-cause visits | T3 | 0.95 | +21.8 [+15.2, +28.4] min, +2.1 pts | +10.6 [+5.2, +16.2] min, +1.7 pts | -11.2 [-14.2, -8.2] min, -0.4 pts |
| several complaints, no shared cause | T2 | 0.90 | +20.1 [+17.2, +23.4] min, +0.6 pts | +8.9 [+7.3, +10.8] min, -1.0 pts | -11.1 [-13.8, -8.9] min, -1.6 pts |
| several complaints, no shared cause | T2 | 0.92 | +19.9 [+17.0, +23.4] min, +0.6 pts | +8.7 [+7.0, +10.5] min, -1.0 pts | -11.2 [-13.9, -9.0] min, -1.6 pts |
| several complaints, no shared cause | T2 | 0.94 | +17.9 [+14.9, +21.2] min, +0.6 pts | +6.7 [+5.1, +8.5] min, -1.0 pts | -11.2 [-13.9, -9.0] min, -1.6 pts |
| several complaints, no shared cause | T2 | 0.95 | +18.0 [+15.0, +21.5] min, +0.7 pts | +6.7 [+5.1, +8.5] min, -1.0 pts | -11.3 [-14.1, -9.0] min, -1.7 pts |
| several complaints, no shared cause | T3 | 0.90 | +24.4 [+21.7, +27.7] min, +4.9 pts | +3.4 [+2.9, +4.0] min, +0.6 pts | -21.0 [-24.0, -18.5] min, -4.3 pts |
| several complaints, no shared cause | T3 | 0.92 | +25.0 [+22.4, +28.2] min, +4.9 pts | +4.4 [+3.8, +5.0] min, +0.6 pts | -20.6 [-23.6, -18.2] min, -4.3 pts |
| several complaints, no shared cause | T3 | 0.94 | +25.2 [+22.6, +28.3] min, +4.9 pts | +4.4 [+3.8, +5.1] min, +0.5 pts | -20.8 [-23.6, -18.2] min, -4.4 pts |
| several complaints, no shared cause | T3 | 0.95 | +23.9 [+21.2, +27.0] min, +5.0 pts | +4.0 [+3.3, +4.6] min, +0.5 pts | -19.9 [-22.7, -17.4] min, -4.4 pts |
| all visits | T2 | 0.90 | +5.6 [+4.1, +7.1] min, +0.4 pts | +1.8 [+0.7, +2.9] min, -0.1 pts | -3.7 [-4.6, -3.0] min, -0.5 pts |
| all visits | T2 | 0.92 | +6.1 [+4.6, +7.6] min, +0.4 pts | +2.3 [+1.3, +3.4] min, -0.0 pts | -3.8 [-4.7, -3.0] min, -0.5 pts |
| all visits | T2 | 0.94 | +6.6 [+5.3, +8.2] min, +0.5 pts | +2.9 [+1.9, +4.0] min, +0.0 pts | -3.7 [-4.7, -3.0] min, -0.5 pts |
| all visits | T2 | 0.95 | +6.3 [+4.9, +8.0] min, +0.6 pts | +2.5 [+1.5, +3.7] min, +0.1 pts | -3.8 [-4.7, -3.0] min, -0.5 pts |
| all visits | T3 | 0.90 | +7.8 [+6.6, +9.2] min, +1.5 pts | +0.5 [-0.0, +1.0] min, +0.3 pts | -7.3 [-8.5, -6.3] min, -1.3 pts |
| all visits | T3 | 0.92 | +8.1 [+6.9, +9.5] min, +1.5 pts | +0.8 [+0.3, +1.3] min, +0.3 pts | -7.3 [-8.4, -6.3] min, -1.3 pts |
| all visits | T3 | 0.94 | +9.2 [+7.8, +10.6] min, +1.7 pts | +1.7 [+1.0, +2.4] min, +0.4 pts | -7.4 [-8.5, -6.4] min, -1.3 pts |
| all visits | T3 | 0.95 | +9.9 [+8.5, +11.5] min, +1.7 pts | +2.7 [+1.8, +3.6] min, +0.4 pts | -7.2 [-8.3, -6.2] min, -1.3 pts |


# Deviations from FIRST_DEMO_NOTES.md (logged before the corrected run)

## D1: the demo's live question "does this box have reheat?" is declared as yes

What was seen: the first run stopped at the first step with `the tool asked 'reheat'`, before any result existed. The first demo's `build_cases()` declares only `instrument` and `occupant`; the technician is asked about reheat live, and a simulation cannot answer a question.
What changed, in the script only: the cases are rebuilt with the demo's own constants (`BUILDING`, `ITEMS`, `MIN_RATE`, `ROOM_IDS`, imported from its server, read-only) and a context that adds `reheat="yes"` (the example building has reheat points on its boxes). Nothing else differs from the demo's configuration. Gate G2 now also asserts the declared context.

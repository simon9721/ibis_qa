This document is to record what i think the markdown quality report should look like.
Or maybe we should directly generate HTML reports? since I think it handle images better.

1. Summary: IQ Candidate Score, some comments

2. Then each quality check items both pass and fail with explanations. there should be a table of contents section that allow user to quickly navigate to a check item or go back to table of contents.

Group by Level (1-4) and sort by Type (component, Model, ...)

Level 1 Check:
2.1 IBISCHK result: PASS/FAIL
If fail, list errors by IBISCHK
IBISCHK results message show here (if any)

Level 2 Check:
3.1.1
stragithforward, exist or not. if missing, show which line in the IBIS file the issue come from. (also for all other items, if FAIL, show source)

Level 3 Check:

Level 4 Check: (if enable by max level selection, let's make dafult to level 3)

I will only list items that need special attention here.

5.3.2 & 5.3.6 & 5.3.7 and use same figure. in this figure show the combined curves (pullup+power clamp combined & pulldown&ground clamp combined, this is correct right?)

5.3.8/5.3.9: use zoomed in view to show the near zero volt section

5.3.10: put two clamp tables into one (which we already have), then zoom in to show the 0-Vcc range

5.5.3/5.5.4 if FAIL/WARN, should how much is it out of range. same for other applicable items, if FAIL/WARN, show actual vs. allow values

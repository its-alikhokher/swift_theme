## What this changes

<!-- What broke, or what is new. One or two sentences is plenty. -->

## Why

<!-- If this is a fix: what the failure actually was. A theme fails quietly, so
     "the accent was the wrong colour" is less useful than "the rule read a
     variable no theme defines, so it fell back to Frappe's blue". -->

## Screenshots

<!-- Required for anything visual — a colour or layout change cannot be
     reviewed from a diff. Before and after, if you can. -->

## Checks

- [ ] `bench --site … run-tests --app swift_theme` passes
- [ ] `node swift_theme/tests/boot_js_contract.js` passes
- [ ] If this fixes a bug, there is a test that fails without the fix
      <!-- Break the fix on purpose and confirm the test goes red. A test that
           still passes against the bug it was written for is worse than none. -->
- [ ] If a preset or palette changed, `scripts/generate_theme_css.py` was re-run
- [ ] No `transform`, `filter`, `backdrop-filter`, `content-visibility` or
      `contain` added to a desk container — see CONTRIBUTING.md for why
- [ ] No hardcoded colour inside a `[data-swift-themed]` rule

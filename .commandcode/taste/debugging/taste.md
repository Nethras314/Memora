# Debugging & Verification Preferences

- For UI/rendering defects, expects the underlying root cause to be identified before fixing — diagnosis grounded in the actual code path (e.g. a layout regression traced to a specific CSS positioning class) rather than symptom patching — and then the fix applied directly in the existing codebase. Confidence: 0.7
- Verifies visual/UI changes in an actual rendered browser (screenshots at desktop and mobile widths) rather than relying on a successful build/compile; a passing build is explicitly not treated as proof the UI is correct. Confidence: 0.65

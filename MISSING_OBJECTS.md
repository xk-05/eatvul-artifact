# Missing Objects and Why They Matter

The current public AST-token-only setting does not include the following
objects:

- true inserted spans;
- source diffs;
- source-to-token mappings;
- CFGs;
- PDGs;
- compiler-validated adaptive snippets;
- complete paired prediction logs for all defense layers.

These missing objects matter because they are the evidence required to validate
source-aware deletion and dependence isolation. Whole-sample detection and
quarantine can be evaluated from serialized AST-token sequences and detector
outputs. Reliable source-level sanitization, however, requires exact source
boundaries, syntax validation, reachability, dependence information, and paired
before/after prediction traces.

The paper's negative diagnostic deletion result should therefore be read as a
capability-boundary claim, not as a claim that every possible token-only method
has been exhausted.

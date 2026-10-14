# Contributing

Observation Receipt is an early local-first project. Contributions should preserve its evidence boundaries.

## Before opening a change

1. Name the user-facing claim or failure the change addresses.
2. Prefer a new fixture or mutation that fails before the code change.
3. Keep unknown timing, missing capability, witness dependence, and measurement incompleteness explicit.
4. Do not add a dependency when the standard library or current code can satisfy the accepted behavior.
5. Run the complete standalone test suite.

## Pull-request evidence

Include:

- the behavior changed;
- the smallest reproducing case;
- the tests run;
- any new data or privacy burden;
- any claim ceiling that changed; and
- one failure or counterfactual path exercised.

Do not include credentials, private participant data, copyrighted source files without distribution permission, or claims accepted on behalf of a scientific or operational authority.

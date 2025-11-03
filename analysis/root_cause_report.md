# Reverse-Engineered Root Cause Report

This document summarizes the primary reasons the automated test and quality
checks fail in the current `connascence-safety-analyzer` codebase. The findings
come from reviewing failing pytest output and correlating it with the
implementation.

## 1. CLI does not recognise the `scan` subcommand

Multiple end-to-end CLI workflows invoke the analyzer as `connascence scan …`.
The test harness builds argument lists that start with the literal string
`"scan"`, e.g. `cli.run(["scan", path, "--format", "json"])`.【F:tests/e2e/test_cli_workflows.py†L305-L347】

However, the CLI parser only treats positional arguments as file system paths
and does not define or special-case a `scan` command. `_validate_paths` therefore
attempts to resolve a path literally named `scan`, triggers the "file not
found" error handler, and returns `EXIT_INVALID_ARGUMENTS` (exit code 3).【F:interfaces/cli/connascence.py†L72-L179】【F:interfaces/cli/connascence.py†L205-L220】

*Recommended remediation:* extend the CLI to either register a `scan`
subcommand or strip it before path validation so that existing workflows no
longer fail with invalid-path errors.

## 2. Workflow validator assumes `store_test_scenario`

The shared `SequentialWorkflowValidator` persists each scenario by calling
`self.memory.store_test_scenario(...)`.【F:tests/e2e/test_cli_workflows.py†L93-L121】
Enterprise-scale tests reuse this validator but pass the global
`EnterpriseScaleCoordinator` instance, which implements several storage helpers
but **no** `store_test_scenario` method.【F:tests/e2e/test_enterprise_scale.py†L42-L111】【F:tests/e2e/test_enterprise_scale.py†L692-L720】
At runtime the validator therefore raises `AttributeError`, causing every
enterprise-scale scenario to fail before performing any assertions.

*Recommended remediation:* add a `store_test_scenario` method (or compatible
adapter) to `EnterpriseScaleCoordinator`, or teach the validator to tolerate
coordinators without that API.

## 3. Interface contract mismatch with compliance tests

The compliance meta-tests assert that the shared agent interface exposes a rich
LLM-style contract including messaging, embeddings, reranking, health checks,
and more.【F:tests/fixtures/test_connascence_compliance.py†L358-L388】 The current
`InterfaceBase` only defines basic display and error-handling hooks and lacks
all of the required surface area.【F:interfaces/core/interface_base.py†L20-L159】
As a result the test immediately reports missing methods for every expected
capability.

*Recommended remediation:* expand `InterfaceBase` (and concrete implementations)
to provide the expected agent-facing API, or adjust the compliance test if the
contract was intentionally reduced.

## 4. Missing `tests.agents` package for architectural compliance

Several architectural compliance checks import fixtures from a
`tests.agents` namespace, but no such package exists in the repository. The
first import attempt (`tests.agents.core.fixtures.conftest`) raises
`ModuleNotFoundError`, aborting the test run.【F:tests/fixtures/test_connascence_compliance.py†L440-L507】

*Recommended remediation:* add the expected `tests/agents` support package or
update the compliance tests to reference the actual location of agent fixtures.

## 5. Meta-tests flag pervasive isolation violations

`test_test_isolation_patterns` scans every test file for global variables,
`os.environ` usage, direct file I/O, or `time.sleep` calls and fails if any are
present.【F:tests/fixtures/test_connascence_compliance.py†L390-L437】 The project
contains numerous legitimate uses of these patterns (for example, the CLI and
integration suites manipulate files and sleep for timing), so the compliance
check currently reports more than one hundred violations. This behaviour causes
consistent failures across quality gates even though the flagged patterns are
expected for these tests.

*Recommended remediation:* either relax the meta-test to whitelist known-safe
patterns or refactor the affected tests to use fixtures/temp directories so
that the compliance gate reflects actionable issues.

---

Addressing the issues above will unblock the highest-impact failing checks and
allow further triage of the remaining test failures.

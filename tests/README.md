# Test Suite

This directory contains test suites for the AI configuration scripts and
deployment contracts.

## Research Report Location Tests

`test_research_report_locations.py` verifies that cross-agent policy and the
shared reporting skills default durable reports to `docs/research/`, while
allowing explicitly configured exceptions.

```bash
python3 tests/test_research_report_locations.py
```

## FOSS Comparison Reporting Tests

`test_foss_comparison_reporting.py` verifies accessible traffic-light matrix
ratings, optional facet matrices, and the existing coloured verdict contract
used by similar Pi package audit reports.

```bash
python3 tests/test_foss_comparison_reporting.py
```

## Background Human-Attention Tests

`test_background_human_attention.py` verifies that `/bg`, `/bgp`, and `/bed`
keep human-needed beads out of automatic queues, flag and clear them with a
durable checklist, and surface `bd human list` at unattended handoff.

```bash
python3 tests/test_background_human_attention.py
```

## AI Cockpit Contract Tests

`test_ai_cockpit_contract.py` validates the target-neutral orchestrator contract,
placeholder-only environment inventory, required security prohibitions, stable
volume names, and absence of common instance-specific identifiers.

```bash
python3 tests/test_ai_cockpit_contract.py
```

## ai-safe-rm Tests

`test_ai_safe_rm.py` - Comprehensive test suite for the `ai-safe-rm`
script.

### Running the tests

```bash
# Run all tests
python3 tests/test_ai_safe_rm.py

# Run with verbose output
python3 tests/test_ai_safe_rm.py -v

# Run specific test
python3 tests/test_ai_safe_rm.py TestAiSafeRm.test_modified_tracked_file_backed_up
```

### Test coverage

The test suite covers:

- **Unmodified tracked files** - Should be deleted directly
- **Modified tracked files** - Should be backed up to `.safe-rm/`
- **Untracked files** - Should be backed up to `.safe-rm/`
- **Multiple files** - Mixed statuses handled correctly
- **Subdirectories** - Path preservation in backups
- **Directory deletion** - Requires `-r` flag
- **Directory optimization** - All unmodified tracked uses `rm -rf`
- **Directory recursion** - Selective backup when mixed content
- **Nested structures** - Deep directory hierarchies
- **Hash collisions** - Multiple versions with same filename
- **Empty directory cleanup** - Removes empty dirs after processing
- **Error handling** - Non-existent files, not in git repo

All tests run in isolated temporary git repositories and clean up
after themselves.

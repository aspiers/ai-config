# Test Suite

This directory contains test suites for the AI configuration scripts.

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

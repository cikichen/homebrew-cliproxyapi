# CLIProxyAPI Formula Auto-Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a lightweight automation flow that updates `Formula/cliproxyapi.rb` to the latest upstream CLIProxyAPI release and pushes the change automatically.

**Architecture:** A small Python script fetches the latest GitHub release metadata and `checksums.txt`, updates the formula version and macOS SHA-256 values, and exits cleanly when there is no change. A GitHub Actions workflow runs the script on a schedule or manual trigger and commits the formula update back to `main` only when the file changed.

**Tech Stack:** Python 3 standard library, GitHub Actions, Homebrew formula Ruby file.

---

### Task 1: Write the failing tests for formula update logic

**Files:**
- Create: `tests/test_update_formula.py`
- Future implementation: `scripts/update_formula.py`

**Step 1: Write the failing test**
Create tests that expect a script module to expose functions for parsing checksums and updating formula text.

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests.test_update_formula -v`
Expected: FAIL because `scripts/update_formula.py` does not exist yet.

**Step 3: Write minimal implementation**
Create only the functions needed by the tests.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests.test_update_formula -v`
Expected: PASS.

**Step 5: Commit**
Commit test and script together.

### Task 2: Add the update script CLI

**Files:**
- Create: `scripts/update_formula.py`
- Modify: `Formula/cliproxyapi.rb`

**Step 1: Write a failing test for no-op behavior**
Add a test covering unchanged formula content when the latest version already matches.

**Step 2: Run the test to verify it fails**
Run the targeted unittest.

**Step 3: Implement the minimal CLI path**
Make the script fetch release metadata, checksums, update the file, and print whether a change was made.

**Step 4: Run tests**
Run the full unittest file again and expect PASS.

### Task 3: Add GitHub Actions automation

**Files:**
- Create: `.github/workflows/update-formula.yml`
- Modify: `README.md`

**Step 1: Write workflow requirements into the README**
Document manual and scheduled update behavior.

**Step 2: Implement workflow**
Run the Python script on schedule and workflow dispatch, commit only if `Formula/cliproxyapi.rb` changed.

**Step 3: Verify workflow YAML and docs**
Read files back and inspect for correctness.

### Task 4: Final verification and push

**Files:**
- Verify: `tests/test_update_formula.py`
- Verify: `Formula/cliproxyapi.rb`
- Verify: `.github/workflows/update-formula.yml`
- Verify: `README.md`

**Step 1: Run tests**
Run: `python3 -m unittest tests.test_update_formula -v`
Expected: PASS.

**Step 2: Run Homebrew checks**
Run: `brew style Formula/cliproxyapi.rb` and `brew audit --strict cikichen/cliproxyapi/cliproxyapi`
Expected: PASS.

**Step 3: Commit and push**
Create atomic commits and push to GitHub.

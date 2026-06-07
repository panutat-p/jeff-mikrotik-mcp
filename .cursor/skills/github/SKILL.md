---
name: gh-pr
description: Use GitHub CLI (gh) to create a PR, review an existing PR, or add/update details on a PR. Use when the user asks to open a PR, create a pull request, review a PR, update PR description, add reviewers, or any gh pr workflow.
disable-model-invocation: true
---

# GitHub CLI PR Workflow

## Before Any Command

Always verify authentication first:

```bash
gh auth status
```

If not authenticated, run `gh auth login` before proceeding.

## Create a PR

### PR Title

Use a **plain English sentence** that describes the change for a human reader.

- Good: `Fix white overscroll section on iPad Home page`
- Good: `Add refund security deposit form validation`
- Bad: `fix(crm-ui): remove white overscroll section on iPad`
- Bad: `feat: add validation`, `chore: update deps`

Do **not** use conventional commit prefixes (`feat:`, `fix:`, `chore:`, etc.) or scoped commit formats (`fix(scope): ...`) in PR titles.

### PR Body

Always include these sections, in this order:

1. **Problem** — What is broken or missing? Where does it show up?
2. **Root Cause** — Why it happens (invalid markup, missing CSS, wrong layout math, etc.)
3. **Solution** — What was changed and why that fixes it
4. **Affected Files** — Table or bullet list of changed files with a short note per file
5. **Test Plan** — Manual verification checklist

Optional: add a diagram (mermaid) when the bug involves layout, data flow, or before/after behavior.

### Create PR

1. Create PR with title and body:

   ```bash
   gh pr create --title "Fix white overscroll section on iPad Home page" --body "$(cat <<'EOF'
   ## Problem

   On iPad Safari, swiping past the bottom of the Home page reveals a white section below the app content.

   ## Root Cause

   - `LayoutView.vue` used an invalid `<body>` tag inside Vue-managed DOM, so `bg-stone-300` never applied to the real document
   - `html`/`body` had no background color, so iOS overscroll bounce showed white
   - `<main>` used `min-h-screen` below a header, making the page taller than the viewport

   ## Solution

   - Replace `<body>` with a flex column wrapper using `min-h-dvh`
   - Change `<main>` to `flex-1` so it fills space below the header
   - Set `background-color: theme(--color-stone-300)` on `html, body`

   ## Affected Files

   | File | Change |
   |------|--------|
   | `apps/crm-ui/src/views/LayoutView.vue` | Valid wrapper div + `flex-1` main |
   | `apps/crm-ui/src/index.css` | Global stone-300 background on `html, body` |

   ## Test Plan

   - [ ] Open HomeView on iPad Safari
   - [ ] Overscroll past the bottom and confirm stone-300, not white
   - [ ] Verify layout on desktop and mobile
   EOF
   )"
   ```

2. Add reviewers or assignees (optional):

   ```bash
   gh pr create --title "..." --body "..." --reviewer handle1,handle2 --assignee "@me"
   ```

3. Draft PR (not ready for review):

   ```bash
   gh pr create --draft --title "..." --body "..."
   ```

4. Autofill title and body from commit messages (only when appropriate):

   ```bash
   gh pr create --fill
   ```

   After `--fill`, **edit the title and body** to match the conventions above. Commit messages often use conventional prefixes; PR titles and bodies should not.

## View / Review a PR

```bash
# View PR in terminal
gh pr view [number]

# Open PR in browser
gh pr view [number] --web

# List open PRs
gh pr list

# View PR diff
gh pr diff [number]

# View PR checks / CI status
gh pr checks [number]

# Watch checks until they finish
gh pr checks [number] --watch
```

## Add or Update PR Details

```bash
# Set title
gh pr edit [number] --title "new title"

# Replace body
gh pr edit [number] --body "new body text"

# Add reviewers
gh pr edit [number] --add-reviewer handle1,handle2

# Remove reviewers
gh pr edit [number] --remove-reviewer handle1

# Add labels
gh pr edit [number] --add-label "bug,enhancement"

# Remove labels
gh pr edit [number] --remove-label "needs-triage"

# Mark ready for review (un-draft)
gh pr ready [number]

# Convert back to draft
gh pr ready [number] --undo
```

## Approve / Request Changes

```bash
# Approve
gh pr review [number] --approve

# Request changes with comment
gh pr review [number] --request-changes --body "Please fix X"

# Leave a comment review
gh pr review [number] --comment --body "Looks good overall, minor nits inline"
```

## Merge a PR

```bash
# Merge commit
gh pr merge [number] --merge

# Squash merge
gh pr merge [number] --squash

# Rebase merge
gh pr merge [number] --rebase

# Auto-merge when checks pass
gh pr merge [number] --auto --squash

# Delete branch after merge
gh pr merge [number] --squash --delete-branch
```

## Tips

- Omit `[number]` to target the PR for the current branch.
- Use `--web` on any command to open that PR in the browser.
- `gh pr view --json title,body,reviews,reviewRequests` for structured data.
- When updating an existing PR with `gh pr edit --body`, keep the same required sections: Problem, Root Cause, Solution, Affected Files, Test Plan.

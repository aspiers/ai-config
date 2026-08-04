---
name: github-attachments
description: Upload images and files to GitHub PRs, issues, and comments so GitHub hosts them instead of committing binaries to the repository. Use when adding screenshots to a PR or issue body, replacing committed screenshots or raw.githubusercontent.com links with hosted attachments, or when `gh` appears to offer no way to attach a file.
---

# GitHub Attachments Without Committing Binaries

Screenshots attached to a PR are review ephemera. Committing them puts
binaries in git history forever — bloating every clone, with no value to the
codebase. The historical workaround (commit the image, link it via a
`raw.githubusercontent.com` URL pinned to a SHA) is the anti-pattern this
skill replaces.

`gh` has no attachment support: no flag on `gh pr create`, `gh pr edit`,
`gh issue create`, or `gh issue comment`. The GraphQL API has no upload
mutation. But an undocumented endpoint produces exactly the
`https://github.com/user-attachments/assets/<uuid>` URLs that browser
drag-and-drop produces, and it works from `curl` with a `gh` token.

**This endpoint is undocumented and unofficial. GitHub could change or
remove it without notice.** Verified working against github.com on
2026-08-04.

## Upload one file

```bash
FILE=screenshot.png
REPO_ID=$(gh api repos/OWNER/REPO --jq .id)
TOKEN=$(gh auth token)

curl -sS -X POST \
  "https://uploads.github.com/user-attachments/assets?name=$(basename "$FILE")&content_type=image/png&repository_id=$REPO_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  --data-binary "@$FILE"
```

HTTP 201 with `{"url":"https://github.com/user-attachments/assets/<uuid>"}`.

`content_type` must match the file (`image/png`, `image/jpeg`, ...). Any
repository the token can push to works.

Reference the returned URL as ordinary markdown in the body:

```markdown
![Login screen](https://github.com/user-attachments/assets/<uuid>)
```

Then apply it: `gh pr edit N --body-file body.md` (or `gh issue edit`,
`gh pr comment --body-file`, ...).

## Order matters: upload, reference, *then* verify

**An uploaded asset returns HTTP 404 with a 9-byte "Not Found" body until
some PR or issue body actually references it.** The upload returns 201 and a
valid URL immediately, but the URL does not resolve until it is referenced.

This is not propagation delay. Waiting does not help, and re-uploading only
creates orphaned assets. Do not diagnose a 404 at this stage as a failed
upload.

So:

1. Upload every file, recording the name→URL mapping as you go.
2. Rewrite the PR/issue body to reference the new URLs.
3. Apply the body with `gh pr edit` / `gh issue edit`.
4. **Only then** verify the assets resolve.

Verify by byte count against the source, not by HTTP status —
`curl -o /dev/null -w '%{http_code}' -L` can report a misleading status:

```bash
exp=$(wc -c < "$FILE")
got=$(curl -sS -L --max-time 30 "$URL" | wc -c)
[ "$exp" = "$got" ] || echo "MISMATCH: expected $exp, got $got"
```

A 9-byte response is the literal string `Not Found` — the asset is not
referenced anywhere yet.

## Bulk uploads and migrations

For several files, append each `name<TAB>url` pair to a TSV as you upload,
then do the body rewriting with a small Python regex substitution over that
mapping. That keeps the fragile per-file step separate from the fragile
body-rewriting step, so a failure in one does not force redoing the other.

Under `zsh` with `noclobber` set, `>` and `>>` silently fail when
creating or overwriting a file — which can silently lose the whole mapping.
Use `: > mapping.tsv` to create it, or pipe through `tee -a`.

To migrate screenshots already committed to a repository:

1. Extract the blobs with `git show <sha>:<path> > out.png`. They may live
   on commits no longer reachable from any branch, so find the SHA from the
   PR's commit list or the reflog rather than assuming `HEAD` has them.
2. Upload them and rewrite the PR bodies to the new URLs.
3. Verify (order above), then `git rm` the files.

`git rm` removes the files from the tree but not the blobs from history;
purging those requires rewriting history, which is rarely worth it for a few
small images.

## Alternatives

`gh` CLI extensions such as `gh-image` wrap this same endpoint, and
cli/cli#12960 requests native support. The raw `curl` above needs no
dependencies.

Endpoint credit:
<https://island94.org/2026/08/programmatically-upload-attachments-to-github-issues-pull-requests-comments>

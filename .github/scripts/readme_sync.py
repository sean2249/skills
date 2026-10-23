"""readme-sync check: fails a PR that changes README.md without README.zh-TW.md.

Run by .github/workflows/readme-sync.yml. Inputs are environment variables:
LABELS (JSON array of label names), REPO, PR, BASE_REF, GH_TOKEN.
For local tests, FILES_JSON (JSON array of {filename, status, previous_filename}) and
BASE_ZH_STATUS (HTTP status, e.g. 200 / 404 / 500) replace the two API calls.
"""
import json, os, subprocess, sys, urllib.parse

EN, ZH = "README.md", "README.zh-TW.md"
SKIP = "readme-sync: skip"


def base_zh_status():
    if "BASE_ZH_STATUS" in os.environ:
        return os.environ["BASE_ZH_STATUS"].strip(), ""
    # Resolve the base branch to its current sha, not the event's base.sha: that sha can predate
    # the Chinese file landing on the base branch, and a later run on the same PR would still pass.
    # Resolving first also keeps a missing branch from looking like a missing file (both are 404).
    repo = os.environ["REPO"]
    b = subprocess.run(
        ["gh", "api", f"repos/{repo}/branches/{urllib.parse.quote(os.environ['BASE_REF'], safe='')}",
         "--jq", ".commit.sha"],
        capture_output=True, text=True,
    )
    sha = b.stdout.strip()
    if b.returncode != 0 or not sha:
        return "", f"could not resolve base branch: {b.stderr.strip()}"
    # -i prints the status line first; gh exits 1 on 404 and on every other error alike,
    # so the status line, not the exit code, tells "not set up yet" apart from a failure.
    r = subprocess.run(
        ["gh", "api", "-i", f"repos/{repo}/contents/{ZH}?ref={sha}"],
        capture_output=True, text=True,
    )
    first = r.stdout.splitlines()[0] if r.stdout else ""
    parts = first.split()
    if len(parts) >= 2 and parts[0].startswith("HTTP/") and parts[1].isdigit():
        return parts[1], r.stderr.strip()
    return "", r.stderr.strip() or first


def changed_files():
    if "FILES_JSON" in os.environ:
        return json.loads(os.environ["FILES_JSON"])
    out = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{os.environ['REPO']}/pulls/{os.environ['PR']}/files",
         "--jq", ".[] | {filename, status, previous_filename}"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]  # one object per line


def main():
    labels = json.loads(os.environ.get("LABELS") or "[]")
    if SKIP in labels and "risk: low" in labels:
        sys.exit('::error::"readme-sync: skip" cannot be combined with "risk: low"; a PR that skips '
                 'this check is merged by the author. Change the risk label to "risk: medium" or '
                 'remove the skip label.')
    if SKIP in labels:
        print('Label "readme-sync: skip" is set; check skipped.')
        return

    status, detail = base_zh_status()
    if status == "404":
        print(f"{ZH} is not on the base branch yet; nothing to check.")
        return
    if status != "200":
        sys.exit(f"::error::Could not tell whether {ZH} is on the base branch "
                 f"(HTTP status {status or 'unknown'})" + (f": {detail}" if detail else "."))

    files = changed_files()
    if any((f.get("status") == "removed" and f.get("filename") == ZH)
           or (f.get("status") == "renamed" and ZH in (f.get("filename"), f.get("previous_filename")))
           for f in files):
        sys.exit(f"::error::This PR removes or renames {ZH}. Keep the file, or the author adds the "
                 f'"{SKIP}" label and merges by hand.')

    names = {f.get("filename") for f in files} | {f.get("previous_filename") for f in files}
    if EN in names and ZH not in names:
        sys.exit(f"::error::{EN} changed but {ZH} did not. Update {ZH} in this PR, or, if only one "
                 f'of them should change, the author adds the "{SKIP}" label and merges by hand.')
    print(f"{EN} and {ZH} are in sync for this PR.")


if __name__ == "__main__":
    main()

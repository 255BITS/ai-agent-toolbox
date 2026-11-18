"""Publish the tested commit when a main merge changes the package version."""

import argparse
import ast
import json
import os
import re
import subprocess
import tomllib
from importlib.metadata import version
from pathlib import Path


def output(*args, input=None):
    return subprocess.check_output(args, text=True, input=input).strip()


def declared_version(path, contents):
    if path.name == "pyproject.toml":
        return tomllib.loads(contents)["project"]["version"]
    versions = [
        ast.literal_eval(keyword.value)
        for node in ast.walk(ast.parse(contents))
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) == "setup" or getattr(node.func, "attr", None) == "setup")
        for keyword in node.keywords
        if keyword.arg == "version"
    ]
    if len(versions) != 1:
        raise ValueError("Expected one static setup.py package version")
    return versions[0]


def qualify(package, before):
    from packaging.version import Version

    metadata = Path("pyproject.toml" if Path("pyproject.toml").is_file() else "setup.py")
    current = Version(declared_version(metadata, metadata.read_text()))
    if current != Version(version(package)):
        raise ValueError("Source version differs from the installed tested wheel")
    if not before or before == "0" * 40:
        return
    if not re.fullmatch(r"[0-9a-f]{40}", before):
        raise ValueError("Expected the full commit before the main push")
    previous_files = output("git", "ls-tree", "--name-only", before, "--", "pyproject.toml", "setup.py").splitlines()
    if not previous_files:
        return
    previous_path = Path("pyproject.toml" if "pyproject.toml" in previous_files else "setup.py")
    previous = Version(declared_version(previous_path, output("git", "show", f"{before}:{previous_path}")))
    if previous != current:
        print(f"version={current}")
        print(f"prerelease={str(current.is_prerelease).lower()}")


def tag_commit(repository, tag):
    ref = f"refs/tags/{tag}"
    result = output("git", "ls-remote", f"https://github.com/{repository}.git", ref, f"{ref}^{{}}")
    refs = {}
    for line in result.splitlines():
        commit, name = line.split("\t")
        refs[name] = commit
    return refs.get(f"{ref}^{{}}", refs.get(ref))


def release_record(repository, tag):
    pages = output(
        "gh", "api", "--paginate", f"repos/{repository}/releases?per_page=100",
        "--jq", f"[.[] | select(.tag_name == {json.dumps(tag)})]",
    )
    records = [record for page in pages.splitlines() for record in json.loads(page)]
    if len(records) > 1:
        raise ValueError(f"Multiple release records use {tag}")
    return records[0] if records else None


def publish(repository, release_version, prerelease):
    source = os.environ["GITHUB_SHA"]
    if (
        os.environ["GITHUB_REPOSITORY"] != repository
        or os.environ["GITHUB_REF"] != "refs/heads/main"
        or os.environ["GITHUB_EVENT_NAME"] != "push"
        or not re.fullmatch(r"[0-9a-f]{40}", source)
        or source != output("git", "rev-parse", "HEAD")
        or not re.fullmatch(r"[0-9][0-9a-z.!+]*", release_version)
    ):
        raise ValueError("Expected a tested main push from the release repository")

    tag = f"v{release_version}"
    current = tag_commit(repository, tag)
    if current not in (None, source):
        raise ValueError(f"{tag} already points to {current}; use a new version")
    record = release_record(repository, tag)
    if record:
        if current != source or record["draft"] or record["prerelease"] != prerelease:
            raise ValueError(f"Existing release state for {tag} requires review")
        print(record["html_url"])
        return

    if current is None:
        output(
            "gh", "api", "--method", "POST", f"repos/{repository}/git/refs",
            "-f", f"ref=refs/tags/{tag}", "-f", f"sha={source}",
        )
    if tag_commit(repository, tag) != source:
        raise ValueError(f"{tag} does not point to the tested commit")
    run = os.environ["GITHUB_RUN_ID"]
    payload = {
        "tag_name": tag,
        "target_commitish": source,
        "name": tag,
        "generate_release_notes": True,
        "prerelease": prerelease,
        "body": f"Tested source commit {source}.\n\n"
                f"[Build and distribution checks](https://github.com/{repository}/actions/runs/{run})",
    }
    record = json.loads(output(
        "gh", "api", "--method", "POST", f"repos/{repository}/releases",
        "--input", "-", input=json.dumps(payload),
    ))
    if record["tag_name"] != tag or record["draft"] or record["prerelease"] != prerelease:
        raise ValueError(f"Unexpected published release state for {tag}")
    if tag_commit(repository, tag) != source:
        raise ValueError(f"{tag} does not point to the tested commit")
    print(record["html_url"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    check = subparsers.add_parser("qualify")
    check.add_argument("--package", required=True)
    release = subparsers.add_parser("publish")
    release.add_argument("--repository", required=True)
    release.add_argument("--version", required=True)
    release.add_argument("--prerelease", required=True, choices=("true", "false"))
    args = parser.parse_args()
    if args.action == "qualify":
        qualify(args.package, os.environ.get("BEFORE_SHA"))
    else:
        publish(args.repository, args.version, args.prerelease == "true")


if __name__ == "__main__":
    main()

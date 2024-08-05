#! /usr/bin/env python
import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE_URL = "https://conda.anaconda.org"
CACHE_DIR = Path("./cache")


def save_to_cache(label: str, subdir: str, repodata: Dict[Any, Any]) -> int:
    filename = CACHE_DIR / f"{label}-{subdir}.json"
    return filename.write_text(json.dumps(repodata))


def read_from_cache(label: str, subdir: str) -> Dict[Any, Any]:
    filename = CACHE_DIR / f"{label}-{subdir}.json"
    if filename.exists():
        return json.loads(filename.read_text())
    else:
        repodata = fetch_all_repodata(label, subdir)
        save_to_cache(label, subdir, repodata)
        return repodata


def fetch_repodata(channel: str, subdir: str) -> Dict[Any, Any]:
    url = f"{BASE_URL}/{channel}/{subdir}/repodata.json"
    resp = requests.get(url)
    resp.raise_for_status()
    repodata = resp.json()
    return repodata


def fetch_all_repodata(
    labels: List[str], subdirs: List[str], cache=False, use_cache=False
) -> Dict[Tuple[str, str], Any]:
    all_repodata = {}
    for label in labels:
        for subdir in subdirs:
            if use_cache:
                repodata = read_from_cache(label, subdir)
            else:
                channel = f"ad-testing/label/{label}"
                repodata = fetch_repodata(channel, subdir)
                if cache:
                    save_to_cache(label, subdir, repodata)
            all_repodata[(label, subdir)] = repodata
    return all_repodata


# name
# version

# subdir
# free-threading

# labels
def is_free_threading(depends: List[str]) -> Optional[bool]:
    for dep in depends:
        if not dep.startswith("python_abi"):
            continue
        if dep.endswith("_cp313t"):
            return True
        return False
    return None


def organize_repodata(
    all_repodata: Dict[Tuple[str, str], Any]
) -> Dict[Tuple[str, str], Dict[Tuple[str, str], List[str]]]:
    pkg_vers = defaultdict(lambda: defaultdict(list))
    for (label, subdir), repodata in all_repodata.items():
        for pkg_fname, pkg_info in repodata["packages"].items():
            name = pkg_info["name"]
            version = pkg_info["version"]
            pkg_subdir = pkg_info["subdir"]
            free_thread = is_free_threading(pkg_info.get("depends", []))
            pkg_vers[(name, version)][(pkg_subdir, free_thread)].append(label)
    return pkg_vers


def find_missing_pkgs(pkg_vers) -> None:
    print("Missing packages:")
    # check for missing packages
    expected_keys = (
        ("osx-arm64", True),
        ("osx-arm64", False),
        ("linux-64", True),
        ("linux-64", False),
    )
    names_to_skip = (
        "python",
        "python_abi",
        "libpython-static",
    )
    for (pkg_name, pkg_ver), stuff in pkg_vers.items():
        if pkg_name in names_to_skip:
            continue
        actual_keys = stuff.keys()
        for expected_key in expected_keys:
            if expected_key not in actual_keys:
                print(pkg_name, pkg_ver, expected_key)


def find_missing_labels(pkg_vers) -> None:
    print("Packages with missing labels:")
    for (pkg_name, pkg_ver), stuff in pkg_vers.items():
        for (subdir, is_free_thread), labels in stuff.items():
            if is_free_thread is None:
                continue
            if is_free_thread:
                for expected_label in ["py313", "py313_nogil"]:
                    if expected_label not in labels:
                        print(pkg_name, pkg_ver, subdir, expected_label)
            else:
                for expected_label in ["py313", "py313_gil"]:
                    if expected_label not in labels:
                        print(pkg_name, pkg_ver, subdir, expected_label)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true")
    args = parser.parse_args()

    subdirs = ["osx-arm64", "linux-64"]
    labels = ["py313", "py313_nogil", "py313_gil"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    all_repodata = fetch_all_repodata(
        labels, subdirs, cache=True, use_cache=args.use_cache
    )
    pkg_vers = organize_repodata(all_repodata)
    find_missing_pkgs(pkg_vers)
    print()
    find_missing_labels(pkg_vers)

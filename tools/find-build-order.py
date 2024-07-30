#! /usr/bin/env python
import argparse
import os.path
from typing import List, Set, Tuple

import yaml
from conda.api import SubdirData
from conda.core.path_actions import CacheUrlAction, ExtractPackageAction
from conda.models.match_spec import MatchSpec
from conda.models.records import PackageRecord


def is_py_dep(name, version, build):
    return "py" in build


class PkgRecipeInfo:
    def __init__(self, prec: PackageRecord, data) -> None:
        self.name = prec.name
        self.version = prec.version
        self.build = prec.build

        reqs = data.get("requirements", {})
        self.build_py, self.build_no_py = self._split_by_type(reqs.get("build"))
        self.host_py, self.host_no_py = self._split_by_type(reqs.get("host"))

        self.run = [MatchSpec(s) for s in reqs.get("run", [])]
        self.test = [MatchSpec(s) for s in data.get("test", {}).get("requires", [])]

    def __repr__(self):
        return f"PkgRecipeInfo(...,{self.name},{self.version},{self.build})"

    def _split_by_type(self, reqs):
        py = {}
        no_py = {}
        if reqs is None:
            return py, no_py
        for req in reqs:
            name, version, build = req.split()
            if is_py_dep(name, version, build):
                py[name] = (name, version, build)
            else:
                no_py[name] = (name, version, build)
        return py, no_py


def read_recipe(prec: PackageRecord, pkg_dir):
    print(f"Reading recipe for: {prec.fn}")
    meta_path = os.path.join(
        pkg_dir,
        prec.fn + ".extract",
        "info",
        "recipe",
        "meta.yaml",
    )
    with open(meta_path) as fh:
        data = yaml.safe_load(fh)
    pi = PkgRecipeInfo(prec, data)
    return pi


def find_match(name, version, string, channels, subdirs) -> PackageRecord:
    ms_str = f"{name}=={version}={string}"
    ms = MatchSpec(ms_str)
    print(f"Matching: {ms}")
    match = SubdirData.query_all(
        ms,
        channels=channels,
        subdirs=subdirs,
    )
    if len(match) == 0:
        if string == "*":
            return find_best_match(MatchSpec(name), channels, subdirs)
        return find_match(name, version, "*", channels, subdirs)
    return match[0]


def find_best_match(ms: MatchSpec, channels, subdirs) -> PackageRecord:
    print(f"Best Matching: {ms}")
    match = SubdirData.query_all(
        ms,
        channels=channels,
        subdirs=subdirs,
    )
    if len(match) == 0:
        if ms.strictness == 3:
            new_ms = MatchSpec(" ".join(ms.spec.split()[:1]))
            return find_best_match(new_ms, channels, subdirs)
        else:
            breakpoint()
    return match[-1]


def download_pkg(prec: PackageRecord, pkg_dir):
    cache_path = os.path.join(pkg_dir, prec.fn)
    if os.path.exists(cache_path):
        return
    print(f"Downloading+Extracting: {prec.url}")
    cache_action = CacheUrlAction(
        url=prec.url,
        target_pkgs_dir=pkg_dir,
        target_package_basename=prec.fn,
    )
    cache_action.execute()
    extract_action = ExtractPackageAction(
        source_full_path=cache_path,
        target_pkgs_dir=pkg_dir,
        target_extracted_dirname=prec.fn + ".extract",
        record_or_spec=prec,
        sha256=prec.sha256,
        md5=prec.md5,
        size=prec.size,
    )
    extract_action.execute()


def collect_recipe_deps(
    to_check, channels, subdirs, pkg_dir
) -> Tuple[List[PkgRecipeInfo], Set[str]]:
    to_check = list(to_check)
    checked = set()
    non_py_deps = set()
    pis = []

    while to_check:
        ms_or_tuple = to_check.pop()

        if isinstance(ms_or_tuple, MatchSpec):
            if ms_or_tuple.name in checked:
                continue
            prec = find_best_match(ms_or_tuple, channels, subdirs)
            checked.add(prec.name)
            if not is_py_dep(prec.name, prec.version, prec.build):
                non_py_deps.add(prec.name)
                continue
        else:
            name, version, string = ms_or_tuple
            if name in checked:
                continue
            prec = find_match(name, version, string, channels, subdirs)
            checked.add(prec.name)

        download_pkg(prec, pkg_dir)
        pi = read_recipe(prec, pkg_dir)
        pis.append(pi)

        for name, info in pi.host_py.items():
            if name in checked:
                continue
            to_check.append(info)

        for name, info in pi.build_py.items():
            if name in checked:
                continue
            to_check.append(info)

        for ms in pi.run:
            if ms.name in checked:
                continue
            to_check.append(ms)

        for ms in pi.test:
            if ms.name in checked:
                continue
            to_check.append(ms)
    return pis, non_py_deps


def show_build_order(pis, non_py_deps, already_built):
    print("Build order:")
    dep_map = {}
    test_map = {}
    for pi in pis:
        deps = (
            list(pi.host_py.keys())
            + list(pi.build_py.keys())
            + [ms.name for ms in pi.run if ms.name not in non_py_deps]
        )
        dep_map[pi.name] = set(deps) - non_py_deps - already_built
        test_deps = set(
            [ms.name for ms in pi.test if ms.name not in non_py_deps] + [pi.name]
        )
        test_map[pi.name] = test_deps - non_py_deps - already_built

    print("---- Already Built ----")
    for name in already_built:
        print(name)
        dep_map.pop(name)
        test_map.pop(name)

    built = set()
    while dep_map or test_map:

        # find the packages that can be built
        can_build = set()
        for name, deps in dep_map.items():
            if len(deps) == 0:
                can_build.add(name)
        # find the packages that can be tested
        can_test = set()
        for name, deps in test_map.items():
            if len(deps) == 0:
                can_test.add(name)
            elif len(deps) == 1 and (name in deps) and (name in can_build):
                can_test.add(name)

        # Show packages that can be built, and mark as built
        print("------------------")
        for name in can_build:
            if name in can_test:
                print(name)
            else:
                print(f"{name} (build-only)")
            dep_map.pop(name)
            built.add(name)
        # Show packages that can be tested
        for name in can_test:
            if name not in can_build:
                print(f"{name} (test)")
            test_map.pop(name)

        # Remove the newly built packages from other package deps
        for name, deps in dep_map.items():
            dep_map[name] = deps - built
        # Remove the newly built packages from test deps
        for name, deps in test_map.items():
            test_map[name] = deps - built

        # If no packages were built or tested the build plan is stuck
        # show the dep map and error out
        if len(can_build) == 0 and len(can_test) == 0:
            for name, deps in dep_map.items():
                print(name, deps)
            raise Exception("No progress in build plan, loop present?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show the build order of a project")
    parser.add_argument(
        "package_spec",
        nargs="+",
        help="List of package specs. The build order will be determined for these packages.",
    )
    parser.add_argument(
        "--channel",
        "-c",
        action="append",
        help="List of channels to search. Can be provided multiple times. If not provided the defaults channel is used",
    )
    parser.add_argument(
        "--already-build",
        "-a",
        action="append",
        help=(
            "List of packages that have already been built. "
            "Can be provided multiple times. "
            "If not provided pip, setuptools, wheel and flit-core are used."
        ),
    )
    parser.add_argument(
        "--pkg-dir",
        default="./pkgs",
        help="Directory to store packages and extracted packages, defaults to ./pkgs",
    )
    parser.add_argument(
        "--subdir",
        default="osx-arm64",
        help="subdir to create build plan for, default is osx-arm64",
    )
    args = parser.parse_args()
    subdirs = [args.subdir, "noarch"]
    to_check = [MatchSpec(spec) for spec in args.package_spec]
    pkg_dir = args.pkg_dir
    default_already_built = ["pip", "setuptools", "wheel", "flit-core"]
    already_built = set(args.already_build or default_already_built)
    default_channels = ["defaults"]
    channels = args.channel or default_channels

    pis, non_py_deps = collect_recipe_deps(to_check, channels, subdirs, pkg_dir)
    show_build_order(pis, non_py_deps, already_built)

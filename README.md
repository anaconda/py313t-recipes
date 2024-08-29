# Python 3.13 threading (i.e., no-GIL) recipes

The submodules in this repository are all branches of [Anaconda recipes](https://github.com/AnacondaRecipes). They can easily be merged upstream if and when necessary.


## General building instructions

- Add `add_pip_as_python_dependency: False` to your `~/.condarc`.

- Either add the `ad-testing/label/py313_nogil` channel to your `.condarc` or always pass it to `conda build`.
  For example, when building `meson`:
  `conda build --no-test -c ad-testing/label/py313_nogil meson-feedstock`

- Always run `conda build` from the top directory in this repository.
  It will pick up the local `conda_build_config.yaml` which contains required configurations.


## Build order for core packages

1. `python`

2. `python_abi`

3. `pip`[^1]

4. These two packages in any order:
   - `setuptools`
   - `flit`[^2]

5. `python-installer`

6. `wheel`

7. `pyproject-matadata`

8. `meson-python`


## Building `meson-python`

`meson python` should be built after the core packages.

Build all packages first with the `--no-test` option, then, once all packages are built, run their tests with `--test`:

Build order:

1. Build these in no specific order:
  - `cython`
  - `meson`
  - `pretend`
  - `pyparsing`
  - `pytest`
  - `poetry-core` (linux only)

2. Build these in no specific order:
  - `packaging`
  - `pyproject-metadata`
  - `pkgconfig` (linux only)

3. `meson-python`


## Building `hatchling` and `hatch-vcs`

`hatchling` can be built after `meson-python` or after the core packages with
minor modification to the build order.

1. Build these in no specific order:
    - `pathspec`
    - `editables`
    - `calver`
    - `pluggy`

2. `trove-clasifiers`

3. `hatchling`

4. `setuptools_scm`

5. `hatch-vcs`


## Building `requests`

`requests` can be built after `hatch-vcs`

Build order:

1. Build these in no specific order:
    * `idna`
    * `certifi`
    * `pysocks`

2. `brotli-python` : one of the outputs from the brotli-feedstock.

3. `urllib3`

4. `requests`


## Building `mypy`

`mypy` can build built after the python core packages.

Build order:

1. Build these in no specific order:
    - `mypy_extensions`
    - `typing_extensions`
    - `types-setuptools`
    - `type-psutil`
    - `psutil`
    - `pytz`

2.  `mypy` (disable MYPYC until we can fix the compiler issues, tests fail)


## Building `rich`

`rich` can be built after the core packages.

Build order:

1. Build these in no specific order:
    - `pygments`
    - `mdurl`

2. `markdown-it-py`

3. `rich`


## Building `numpy` build and test dependencies

These need to be built before `numpy` and depend on various packages above.
After these have been built `numpy` can be built with the `--no-test` option.

Build order for `python-build`

1. `pyproject_hooks`

2. `python-build`


## Building `numpy` test dependencies

These can packages can be built and tested before testing `numpy`.
They can also be built before building `numpy` if desired.

Build order for `pytest-cov`

1. `coverage`

2. `pytest-cov`

Other test dependencies:

1. Build these in no specific order:
    - `black`
    - `versioneer`
    - `pytest-forked`


## Building `numpy` and `pandas`

These require many of the above packages.

Build order:

1. `hypothesis` : build with `--no-test`

2. `attrs`

3. `numpy` : build with `--no-test`

4. Build these in no specific order:
    - `numexpr`
    - `bottleneck`

5. `pandas`

6. `hypothesis` : test existing package or rebuild

7. `numpy` : test existing package or rebuild


## Building Other Packages (1)

These packages can be built after building `hatchling`

1. Build these in no specific order:
    - `filelock`
    - `markupsafe`
    - `fsspec` : recipe in filesystem-spec-feedstock
    - `pyyaml`

2. `jinja2`


[^1]: The current recipe will install files from a wheel file. The package may need to be built again from the source distribution for correctness.
[^2]: The current recipe will only build the `flit-core` package. The recipe will need to be built again without the `bootstrap`` setting to produce the `flit` package.

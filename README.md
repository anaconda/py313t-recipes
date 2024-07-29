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
  - `pyparsing`
  - `pytest`
  - `poetry-core` (linux only)

2. Build these in no specific order:
  - `pyproperty-metadata`
  - `pkgconfig` (linux only)

3. `meson-python`


[^1]: The current recipe will install files from a wheel file. The package may need to be built again from the source distribution for correctness.
[^2]: The current recipe will only build the `flit-core` package. The recipe will need to be built again without the `bootstrap`` setting to produce the `flit` package.

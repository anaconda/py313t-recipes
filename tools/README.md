## Tools to assist with building Python 3.13 conda packages

# find-build-order.py

The `find-build-order.py` script estimates a build order for an existing
package by examing the rendered recipe(s) in the package and dependencies.

For example:

```
❯ ./find-build-order.py "pytest==7.4.4=py312*"
ld order:
---- Already Built ----
flit-core
wheel
setuptools
pip
------------------
typing_extensions
certifi
------------------
setuptools_scm
setuptools-scm
typing-extensions
pyparsing
------------------
iniconfig
packaging
pluggy
------------------
pytest
```

# scan-repo.py

The `scan-repo.py` script looks for packages in the `ad-testing` that are
missing builds for a particular configuration or are missing labels.

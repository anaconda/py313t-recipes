#!/usr/bin/env bash

# ${1}: path to environment, e.g., `~/miniconda3/envs/build`

rm -rf /tmp/conda-bld

for PKG in $(find "${1}/conda-bld" -name '*.tar.bz2' | grep -v '/conda-bld/broken/'); do
  PYTHON_ABI_STRING="$(conda search --info "${PKG}" | grep -- "- python_abi ")"
  ABI=""
  if [[ "${PYTHON_ABI_STRING/_cp313/}" == "${PYTHON_ABI_STRING}" ]]; then
    ABI="none"
  elif [[ "${PYTHON_ABI_STRING%_cp313}" != "${PYTHON_ABI_STRING}" ]]; then
    ABI="GIL"
  elif [[ "${PYTHON_ABI_STRING%_cp313t}" != "${PYTHON_ABI_STRING}" ]]; then
    ABI="free-threading"
  else
    echo "Unknown ABI: ${PYTHON_ABI_STRING}"
  fi
  ARCH_NAME="${PKG#*/conda-bld/}"
  echo "${ARCH_NAME}: ${ABI}"
  mkdir -p "/tmp/conda-bld/${ABI}/${ARCH_NAME%/*}"
  cp -a "${PKG}" "/tmp/conda-bld/${ABI}/${ARCH_NAME}"
done

echo "---"

find /tmp/conda-bld -type f

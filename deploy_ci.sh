#!/usr/bin/env bash

deploy_ci() {

  if [ -z ${TWINE_USERNAME+x} ]; then
    echo "TWINE_USERNAME and TWINE_PASSWORD must be set"
    return 1
  fi

  source venv/bin/activate

  python3 setup.py sdist bdist_wheel
  twine upload dist/*
}

deploy_ci

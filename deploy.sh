#!/usr/bin/env bash

deploy() {
  git add .
  echo "git commit -m $1"
  git commit -m "$1"

  rm -rf dist
  echo "git tag -a $2 -m $1"
  git tag -a $2 -m "$1"
  git push
  git push --tags
  python3 setup.py sdist bdist_wheel
  twine upload dist/*
}

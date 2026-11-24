#!/bin/zsh
# xxj-summer-zjl
cd -- "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  python3.14 -m venv .venv || exit 1
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
.venv/bin/python setup_model.py || exit 1
.venv/bin/python celestial.py

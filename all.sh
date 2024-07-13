#!/bin/bash
find emails/${1} -name *.eml | xargs -I{} bash -c './parse.py "{}" || echo HIBA: {}>&2'

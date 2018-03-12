#!/bin/sh

grep '^VERSION = "[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+"$' scrapbook2zotero.py | grep -o '[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+'

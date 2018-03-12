#!/usr/bin/python
"""
Test suite for scrapbook2zotero migration tool

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

    Copyright (C) 2018 Roman V. Isaev
"""

import filecmp
import os
import subprocess
import scrapbook2zotero

def run_main_and_compare(args, samplefname, tmpfname):
    """ run main with specified args and compare output files
    Args:
        args: args to pass to main
        samplefname: file containing sample output
        tmpfname: file containing results of running main

    If you change output format or contents of scrapbook_test_data,
    then rebuild samples:

        make build_samples
    """
    try:
        os.remove(tmpfname)
    except OSError:
        pass
    scrapbook2zotero.main(args)
    assert filecmp.cmp(samplefname, tmpfname)

def test_1_reading_scrapbook_rdf():
    """ Parse test rdf file and check that we have certain number of entries
    and root is Node object
    """

    scrapbook2zotero.Args.debug = False
    root, items = scrapbook2zotero.open_scrapbook_rdf("scrapbook_test_data")
    assert len(items) == 11
    assert isinstance(root, scrapbook2zotero.Node)

def test_2_standard_run():
    """ Testing default output """
    run_main_and_compare(["scrapbook_test_data", "tmp/test.rdf"],
        "samples/standard.rdf", "tmp/test.rdf")


def test_3_exclude():
    """ Testing --exclude feature, excluding items #1 and #4 """
    run_main_and_compare(["scrapbook_test_data", "tmp/test-exclude.rdf", "--exclude", "1", "4"],
        "samples/standard_1_4_excluded.rdf", "tmp/test-exclude.rdf")

def test_4_win32():
    """ Test win32 build

    Output of windows build running under wine should match samples/standard.rdf
    (with windows newlines converted to unix)
    """

    try:
        os.remove("tmp/test4-windows.rdf")
        os.remove("tmp/test4.rdf")
    except OSError:
        pass
    subprocess.check_call(["wine", "dist/scrapbook2zotero.exe",
                           "scrapbook_test_data", "tmp/test-windows-crlf.rdf"])
    subprocess.check_call(["dos2unix", "-n", "tmp/test-windows-crlf.rdf", "tmp/test-windows.rdf"])
    assert filecmp.cmp("samples/standard.rdf", "tmp/test-windows.rdf")

def test_5_nocoll():
    """ Testing disabling of collection exports (--nocoll flag) """
    run_main_and_compare(["scrapbook_test_data", "tmp/test-nocoll.rdf", "--nocoll"],
        "samples/standard-no-collections.rdf", "tmp/test-nocoll.rdf")

def test_6_notags():
    """ Testing disabling of collection exports (--notags flag) """
    run_main_and_compare(["scrapbook_test_data", "tmp/test-notags.rdf", "--notags"],
        "samples/standard-no-tags.rdf", "tmp/test-notags.rdf")

def test_7_nodedup():
    """ Testing disabling of deduplication (--nodedup flag) """
    run_main_and_compare(["scrapbook_test_data", "tmp/test-nodedup.rdf", "--nodedup"],
        "samples/standard-no-dedup.rdf", "tmp/test-nodedup.rdf")

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

def test_1_reading_scrapbook_rdf():
    """ Parse test rdf file and check that we have certain number of entries
    and root is Node object
    """

    scrapbook2zotero.Args.debug = False
    root, items = scrapbook2zotero.open_scrapbook_rdf("scrapbook_test_data")
    assert len(items) == 9
    assert isinstance(root, scrapbook2zotero.Node)

def test_2_standard_run():
    """ Generate .rdf file from scrapbook_test_data and compare it to
    stored .rdf file from samples/standard.rdf

    If you change output format or contents of scrapbook_test_data,
    rebuild standard.rdf.
    """
    try:
        os.remove("tmp/test2.rdf")
    except OSError:
        pass
    scrapbook2zotero.main(["scrapbook_test_data", "tmp/test2.rdf"])
    assert filecmp.cmp("samples/standard.rdf", "tmp/test2.rdf")

def test_3_exclude():
    """ Generate .rdf file from scrapbook_test_data and compare it to
    stored .rdf file from samples/standard_1_4_excluded.rdf. Entries
    number 1 and 4 are excluded.

    If you change output format or contents of scrapbook_test_data,
    rebuild standard_1_4_excluded.rdf.
    """
    try:
        os.remove("tmp/test3.rdf")
    except OSError:
        pass
    scrapbook2zotero.main(["scrapbook_test_data", "tmp/test3.rdf", "--exclude", "1", "4"])
    assert filecmp.cmp("samples/standard_1_4_excluded.rdf", "tmp/test3.rdf")

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
                           "scrapbook_test_data", "tmp/test4-windows.rdf"])
    subprocess.check_call(["dos2unix", "-n", "tmp/test4-windows.rdf", "tmp/test4.rdf"])
    assert filecmp.cmp("samples/standard.rdf", "tmp/test4.rdf")

def test_5_nocoll():
    """ Generate .rdf file from scrapbook_test_data and compare it to
    stored .rdf file from samples/standard-no-collections.rdf. Testing --nocoll flag.

    If you change output format or contents of scrapbook_test_data,
    rebuild standard.rdf.
    """
    try:
        os.remove("tmp/test5.rdf")
    except OSError:
        pass
    scrapbook2zotero.main(["scrapbook_test_data", "tmp/test5.rdf", "--nocoll"])
    assert filecmp.cmp("samples/standard-no-collections.rdf", "tmp/test5.rdf")

def test_6_notags():
    """ Generate .rdf file from scrapbook_test_data and compare it to
    stored .rdf file from samples/standard-no-tags.rdf. Testing --tags flag.

    If you change output format or contents of scrapbook_test_data,
    rebuild standard.rdf.
    """
    try:
        os.remove("tmp/test6.rdf")
    except OSError:
        pass
    scrapbook2zotero.main(["scrapbook_test_data", "tmp/test6.rdf", "--notags"])
    assert filecmp.cmp("samples/standard-no-tags.rdf", "tmp/test6.rdf")

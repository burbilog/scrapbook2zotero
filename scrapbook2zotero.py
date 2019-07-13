#!/usr/bin/python
""" Export from Scrapbook (Firefox extension) to Zotero

    1. Run this script to generate .rdf file
    2. Import .rdf file to Zotero, it will load scrapbook data with
       all saved images and other files

    If Zotero hangs during import operation, note last record
    number and use --exclude option to exclude that entry.

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

    Loosely based on this: https://bitbucket.org/himselfv/scraptools/src/default/ thus:
    Copyright (C) 2018 somebody from https://bitbucket.org/himselfv/scraptools/src/default
"""

import os
import io
import sys
import time
import argparse
import fnmatch
import rdflib
# import these to help pyinstaller
import rdflib.plugins.memory
import rdflib.plugins.parsers.rdfxml

# Enforce python 2 (for many reasons, including win32 test environment)
assert sys.version_info.major==2, 'Python 2 required'

# SemVer
VERSION = "1.0.2"

def debug(msg):
    """ Print debug message if --debug option was given """
    if Args.debug:
        sys.stderr.write('DEBUG: ' + msg + '\n')

def rdf_to_dict(path):
    """Read and return dictionary of parsed rdf file as dict()
    Args:
        path: Path to scrapbook directory
    Returns:
        A ``Dict`` object with parsed rdf data
    """

    graph = rdflib.Graph()
    graph.parse(path + "/scrapbook.rdf")
    rdf_namespace = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    ns1_namespace = rdflib.Namespace("http://amb.vis.ne.jp/mozilla/scrapbook-rdf#")
    items = dict()

    for itemname, propname, value in graph:

        itemname = itemname.toPython() # to string, or triggers strange behavior
        if itemname.startswith("urn:scrapbook:search"):
            # Dunno what's this but we don't care
            continue
        if itemname.startswith("urn:scrapbook:item"):
            itemname = itemname[18:]
        # There's also urn:scrapbook:root which is a root folder
        item = items.setdefault(itemname, dict())

        propname = propname.toPython()
        if propname.startswith(ns1_namespace):
            propname = 'NS1:'+propname[len(ns1_namespace):]
        elif propname.startswith(rdf_namespace):
            propname = 'RDF:'+propname[len(rdf_namespace):]

        if value.startswith("urn:scrapbook:item"):
            value = value[18:]

        item[propname] = value

        debug("reading itemname='%s', propname='%s'" % (itemname, propname))
    return items

def neuter_name(name):
    """ Makes a string suitable to be file name + id (no equality signs)
    Args:
        name: string to process
    Returns:
        A string without special characters
    """

    reserved_chars = '\\/:*?"<>|='
    for char in reserved_chars:
        name = name.replace(char, '')
    return name

class Node(object): # pylint: disable=too-few-public-methods
    """ Individual node object """

    def __init__(self, nodeid, item):
        # This can be created with item==None, for lost folders
        self.nodeid = nodeid
        self.children = []

        self.type = unicode(item['NS1:type']) if item is not None else ''

        if item is not None:
            title = unicode(item.get('NS1:title', '')) # root has no title
        else:
            title = nodeid

        # Name is a neutered title, suitable for use as filename and ini-id
        self.name = neuter_name(title).strip()
        # Folders in Windows fail when name ends with dots
        # We could've tested for type==folder, but some other types end up as folders too,
        # so it's safer to just prohibit this at all.
        # Spaces too.
        self.name = self.name.rstrip('. ').lstrip(' ')
        if self.name == '':
            self.name = self.nodeid # guaranteed to be safe

        self.comment = unicode(item.get('NS1:comment', '')) if item is not None else ''
        self.source = unicode(item.get('NS1:source', '')) if item is not None else ''

def load_node(nodeid, item, items):
    """ Recursive load nodes from root """

    if 'node' in item:
        return item['node'] # do not create a second one

    node = Node(nodeid, item)
    if node.type == 'folder':
        idx = 1
        while 'RDF:_'+str(idx) in item:
            subitemid = item['RDF:_'+str(idx)]
            subitem = items[subitemid]
            subnode = load_node(subitemid, subitem, items)
            node.children += [subnode]
            idx += 1
    else:
        assert 'RDF:_1' not in item  # should not have child items
        if node.type == 'note':
            # text note
            # title == first line
            # icon can't be changed
            # no formatting
            pass
        elif node.type == 'notex':
            # note with additional formatting
            # title can be changed arbitrarily
            # icon can be changed
            # limited formatting
            pass
        else:
            # saved page
            pass

    item['node'] = node # set backreference
    return node

def fix_lost_items(items, root):
    """Attaches all items without a parent to a root folder"""

    lost_items = 0
    for key, item in items.items():
        if item['node'] is None:
            lost_items += 1
            root.children += [load_node(key, item, items)]
    return lost_items

def subfiles(a_dir):
    """ Return list of files in a_dir

    Args:
      a_dir: directory to scan
    Returns:
      List of files in a_dir
    """
    return [name for name in os.listdir(a_dir)
            if os.path.isfile(os.path.join(a_dir, name))]

def subdirs(a_dir):
    """ Return list of subdirectories in a_dir

    Args:
      a_dir: directory to scan
    Returns:
      List of directories in a_dir
    """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def fix_lost_folders(items, root, path):
    """ Adds an entry for every data directory lacking an entry"""

    lost_folders = 0
    for subdir in subdirs(path + '/data'):
        if subdir in items:
            continue
        debug("found lost folder: %s" % subdir)
        node = Node(subdir, None)
        # try to guess the node type
        files = subfiles(path + '/data/' + subdir)
        if (len(files) == 1) and (files[0].lower() == 'index.html'):
            node.type = "note"
        else:
            node.type = ""
        root.children += [node]
        lost_folders += 1
    return lost_folders

def open_scrapbook_rdf(path):
    """Parse rdf file and turn it to the tree

    Args:
        path: Path to Scrapbook directory
    Returns:
        root: root of the tree
        items: items dict()
    """

    debug("rdf path is " + path)
    items = rdf_to_dict(path)
    items['urn:scrapbook:root']['NS1:type'] = 'folder' # force explicit
    root = load_node('', items['urn:scrapbook:root'], items)
    lost_items = fix_lost_items(items, root)
    if lost_items > 0:
        debug("lost items found: " + str(lost_items))
    lost_folders = fix_lost_folders(items, root, path)
    if lost_folders > 0:
        debug("lost folders found: "+str(lost_folders))

    return root, items

class Counter(object): # pylint: disable=too-few-public-methods
    """ Counter to exclude certain entries """
    def __init__(self):
        self.cnt = 1
        self.uniq = dict()

    def count(self, source):
        """ Count only unique entries """
        if not source in self.uniq:
            self.cnt += 1
            self.uniq[source] = 1

def ampersand(url):
    """ Replace '&' with &amp; to satisfy Zotero importer """
    return url.replace('&', '&amp;')

def export_collections(node):
    """ Export collections

    Args:
        node: root node to export
    Returns:
        Text string with all subcollections as RDF entries
    """

    if node.type == 'folder':
        subcollections = u""
        # collection header
        collection = u"""\n    <z:Collection rdf:about="#collection_{0}">
        <dc:title>{1}</dc:title>""".format(
            node.nodeid, ampersand(node.name))
        for subnode in node.children:
            if subnode.type == 'folder':
                # add link to subcollection
                collection += u'\n        <dcterms:hasPart rdf:resource="#collection_{0}"/>'.format(
                    subnode.nodeid)
                subcollections += export_collections(subnode)
            elif subnode.type != 'note' and subnode.type != 'separator':
                # add link to item
                collection += u'\n        <dcterms:hasPart rdf:resource="{0}"/>'.format(
                    ampersand(subnode.source))
        # collection footer
        collection += u'\n    </z:Collection>'
        # don't generate root collection (name="")
        if node.name == "":
            collection = u""
        return collection+subcollections
    else:
        return u""

def addchain(chain, name):
    """ Generate tags as x/y/z """
    if not Args.disable_tags: # honor --notags flag
        if chain is None:
            return name
        return chain + '/' + name
    return ''

class Deduper(object): # pylint: disable=too-few-public-methods
    """ Deduplication mechanism """
    def __init__(self):
        self.dupes = {}
    def getdupnum(self, title):
        """ Get duplication number

        Args:
            title: item title
        Returns:
            number of dupes in parentheses as unicode string
            or u'' if no dupe.
        """
        # Honor --nodedup flag
        if Args.disable_dedup:
            return u''
        if title in self.dupes:
            self.dupes[title] += 1
            return u' (' + unicode(str(self.dupes[title])) + u')'
        self.dupes[title] = 1
        return u''

def export_node(node, source_dir, tagchain, counter, deduplicator):
    """ Export node

    Args:
        node: node to process
        source_dir: directory to scrapbook data
        tagchain: a chain of tags
        counter: count unique URLs to match items count during import
        deduplicator: deduplicator object
    Returns:
        String with all items as RDF entries
    """

    result = u""

    if node.type == 'folder':
        debug("exporting folder '%s'" % node.nodeid)
        for subnode in node.children:
            result += export_node(subnode, source_dir, addchain(tagchain, node.name),
                                  counter, deduplicator)
    elif node.type == 'note':
        sys.stderr.write("ERROR: 'note' type is not implemented, can't process entry"
                         "'%s'. Skipping.\n" % node.nodeid)
    elif node.type == 'separator':
        # no need to export
        pass
    elif Args.exclude is not None and str(counter.cnt) in Args.exclude:
        debug("excluding node #%d" % counter.cnt)
        counter.count(node.source)
    else: # saved document or notex
        debug("exporting item '%s' source '%s'" % (node.nodeid, node.source))
        # Count unique URLs to track Zotero's import number
        counter.count(node.source)
        # Get reliable node creation time from node id
        nodetime_formatted = time.strftime('%Y-%m-%d %H:%M:%S',
                                           time.strptime(node.nodeid, '%Y%m%d%H%M%S'))
        basedir = "%s/data/%s" % (source_dir, node.nodeid)
        # Check index file existance
        if os.path.isfile(basedir + '/index.html'):
            # typical
            indexfname = basedir + '/index.html'
        elif  os.path.isfile(basedir + '/default.html'):
            # no index.html, hmm. try default.html
            indexfname = basedir + '/default.html'
        else:
            sys.stderr.write("ERROR: failed to export %s entry (#%d), no index.html "
                             "or default.html. Skipping. Try to inspect directory "
                             "'%s/data/%s' and decide what to do with orphaned data.\n"
                             % (node.nodeid, counter.cnt, source_dir, node.nodeid))
            return u""
        # Avoid empty name and source
        if node.name == '':
            node.name = ampersand(node.source)
        if node.source == '':
            node.source = node.nodeid

        # Deduplicate
        node.name = node.name + deduplicator.getdupnum(node.name)

        # Check for PDF files and add them as separate entries
        pdfs = u""
        pdf_links = u""
        pdf_count = 0
        for pdfname in fnmatch.filter(os.listdir(basedir), "*.pdf"):
            pdf_count += 1
            pdf_resource = node.nodeid+'0'+str(pdf_count)
            pdfs += u"""\n    <z:Attachment rdf:about="#item_{0}">
        <z:itemType>attachment</z:itemType>
        <rdf:resource rdf:resource="{1}"/>
        <dc:title>{2}</dc:title>
        <link:type>application/pdf</link:type>
    </z:Attachment>""".format(pdf_resource, os.path.normpath(basedir + '/' + pdfname), pdfname)
            pdf_links += u'\n        <link:link rdf:resource="#item_{0}"/>'.format(
                pdf_resource)
            debug("pdf attachment '%s' added to '%s'" % (pdfname, node.nodeid))

        # document entry
        result += u"""\n    <bib:Document rdf:about="{0}">
        <z:itemType>webpage</z:itemType>
        <dcterms:isPartOf>
           <z:Website></z:Website>
        </dcterms:isPartOf>
        <link:link rdf:resource="#item_{1}"/>{5}
        <dc:subject>{4}</dc:subject>
        <dc:identifier>
            <dcterms:URI>
               <rdf:value>{0}</rdf:value>
            </dcterms:URI>
        </dc:identifier>
        <dcterms:dateSubmitted>{2}</dcterms:dateSubmitted>
        <dc:title>{3}</dc:title>
    </bib:Document>""".format(ampersand(node.source), # {0}
                              node.nodeid, # {1}
                              nodetime_formatted, # {2}
                              ampersand(node.name), # {3}
                              ampersand(tagchain.lstrip('/')), # {4}
                              pdf_links # {5}
                             )
        # attachment entry
        result += u"""\n    <z:Attachment rdf:about="#item_{0}">
        <z:itemType>attachment</z:itemType>
        <rdf:resource rdf:resource="{1}"/>
        <dc:identifier>
            <dcterms:URI>
               <rdf:value>{2}</rdf:value>
            </dcterms:URI>
        </dc:identifier>
        <dcterms:dateSubmitted>{3}</dcterms:dateSubmitted>
        <dc:title>{4}</dc:title>
        <z:linkMode>1</z:linkMode>
        <link:type>text/html</link:type>
    </z:Attachment>""".format(node.nodeid, # {0}
                              os.path.normpath(indexfname), # {1}
                              ampersand(node.source), # {2}
                              nodetime_formatted, # {3}
                              ampersand(node.name) # {4}
                             )
        result += pdfs
    return result

class Args(object): # pylint: disable=too-few-public-methods
    """ Arguments container """
    pass

def parse_args(argv):
    """ Parse argv and store them in dummy Args class """
    parser = argparse.ArgumentParser(
        description="Export from Scrapbook/Scrapbook X to Zotero",
        epilog="""A tool to generate Zotero .rdf import data.
First, export from Scrapbook using this script, then open Zotero, go to
File -> Import and import RDF file and wait for export to finish.
If Zotero hangs during import operation (import counter does not increase
without several minutes), note last record number and exclude it with
--exclude option.
""")
    parser.add_argument('scrapbookdir', action='store', metavar='SCRAPBOOKDIR',
                        help="Source directory, usually somewhere inside mozilla profile")
    parser.add_argument('rdffilename', action='store', metavar='OUTPUT.RDF',
                        help="Output RDF file name. Use '-' to specify standard output.")
    parser.add_argument('--debug', action='store_true',
                        help="Print debug messages")
    parser.add_argument('--exclude', nargs='+', action='store',
                        help="One or more record numbers to exclude")
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    parser.add_argument('--nocoll', action='store_true',
                        help="Disable export of collections")
    parser.add_argument('--notags', action='store_true',
                        help="Disable export of tags")
    parser.add_argument('--nodedup', action='store_true',
                        help="Disable deduplication")
    parsed = parser.parse_args(argv)
    Args.debug = parsed.debug
    Args.exclude = parsed.exclude
    Args.scrapbookdir = parsed.scrapbookdir
    Args.rdffilename = parsed.rdffilename
    Args.disable_collections = parsed.nocoll
    Args.disable_tags = parsed.notags
    Args.disable_dedup = parsed.nodedup

def main(argv):
    """ Main as function, useful to run test from py.test with command line args
    """

    parse_args(argv)

    if Args.exclude is not None:
        debug("excluding entries: " + ','.join(map(str, Args.exclude)))

    # Generate .rdf file from Scrapbook data
    root, items = open_scrapbook_rdf(Args.scrapbookdir)
    debug("# of items loaded: %d" % len(items))
    if Args.rdffilename == '-':
        filehandle = sys.stdout
    else:
        try:
            filehandle = io.open(Args.rdffilename, 'w', encoding='utf-8')
        except IOError:
            sys.stderr.write("ERROR: can't open file '%s' to write.\n" % Args.rdffilename)
            exit(-1)
    #counter = Counter()
    #allitems = export_node(root, Args.scrapbookdir, None, counter)
    # write everything
    filehandle.write(u"""<rdf:RDF
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:z="http://www.zotero.org/namespaces/export#"
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:link="http://purl.org/rss/1.0/modules/link/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:bib="http://purl.org/net/biblio#">""")
    filehandle.write(export_node(root, Args.scrapbookdir,
                                 None, Counter(), Deduper()))
    if not Args.disable_collections:
        filehandle.write(export_collections(root))
    filehandle.write(u"\n</rdf:RDF>")
    filehandle.close()

if __name__ == '__main__':
    main(sys.argv[1:])

# Scrapbook/Scrapbook X to Zotero migration tool

Python script to migrate Scrapbook repository to Zotero. Scrapbook / Scrapbook X is a Firefox note-taking and web page capturing plugin. Zotero is reference management software to manage bibliographic data and related research materials (such as PDF files, HTML files, etc), or, simply put, Scrapbook on steroids.

## Reasons

Alas, Firefox is dying. Mozilla developers decided to scrap Firefox's powerful extensions system and replaced it with Google's lousy webextensions, throwing everybody out of current ecosystem. Thus, all excellent Firefox plugins are obsolete, including many important plugins like Scrapbook. There is no way to re-implement Scrapbook under new restrictions. Also, they push 'Pocket' as a cloud solution, but it's not a replacement for Scrapbook, since everything is kept in their cloud. If they choose to shutdown 'Pocket' product you WILL loose all your data immediately, so don't use 'Pocket'.

Zotero is a mature and stable stand-alone program, able to perform (almost) all Scrapbook tasks. You can install small Zotero plugin called "Zotero connector" (currently there are plugins for Firefox, Chrome and Safari) and use that plugin to capture pages into Zotero's standalone database. Thus your all saved data will be safe and kept in browser-independed place. Also, Zotero can index all your PDF files and provide instant search in all your data, including PDF contents.

Unfortunately, Zotero can't import Scrapbook data directly and Zotero developers said they won't implement import for Scrapbook. So I wrote this script to export Scrapbook repository into Zotero's RDF format. Zotero can import its own files and thus import all Scrapbook data, including complete saved HTML pages and PDFs.

## Installing

### Windows: 

Download scrapbook2zotero.exe from https://github.com/burbilog/scrapbook2zotero/releases 
Open CMD shell in your download directory or place .exe file somewhere in your PATH.
 
### Linux: 

    apt-get install python pip pytest
    pip install rdflib
    git clone https://github.com/burbilog/scrapbook2zotero.git
	cd scrapbook2zotero
	./scrapbook2zotero.py ...

## Usage

    usage: scrapbook2zotero.py [-h] [--debug] [--exclude EXCLUDE [EXCLUDE ...]]
                               [--version] [--nocoll] [--notags] [--nodedup]
                               SCRAPBOOKDIR OUTPUT.RDF

    positional arguments:
      SCRAPBOOKDIR          Source directory, usually somewhere inside mozilla profile
      OUTPUT.RDF            Output RDF file name. Use '-' to specify standard output.

    optional arguments:
      -h, --help            show this help message and exit
      --debug               Print debug messages
      --exclude EXCLUDE [EXCLUDE ...]
                            One or more record numbers to exclude
      --version             show program's version number and exit
      --nocoll              Disable export of collections
      --notags              Disable export of tags
      --nodedup             Disable deduplication


Scrapbook directory is usually something like `C:\Users\Your username\AppData\Roaming\Mozilla\Firefox\[Your Firefox profile]\Scrapbook` on Windows and is something like `~/.mozilla/.firefox/[Your Firefox profile]/Scrapbook` on Linux, unless you've changed that in Scrapbook options. Since it's your data, I'd backup it before doing anything, just in case.

Output file is an RDF data for Zotero import, give it name like import.rdf.

Generate RDF file, then import it into Zotero. During import click `My Library` and watch import counter increase until import is done. **Attention! Sometimes (rare) Zotero fails to import certain saved web pages.** It just hangs. If items counter does not increase for a minute or two then Zotero is stuck. If you have a very large collection, you may stumble upon such a problem. Note stuck import number. Delete already imported data from Zotero, empty trash, re-export Scrapbook data using `--exclude` option to exclude offending entry, then import everything again.

If you don't want to generate collections based on Scrapbook tree structure, use `--nocoll` flag. If you don't want to generate tags based on Scrapbook tree structure, use `--notags` flag. By default, these are features are enabled.

Zotero thinks that pages with equal titles are the same pages. I had hundreds of saved pages from various forums with single title (theme subject). Deduplication feature adds number in parenthesis to each subsequent title to make them unique. Use `--nodedup` flag to disable it. By default this feature is enabled.

## Development information

Prerequisites: python 2.7 for linux and windows, pytest, rdflib. This script was developed on Linux and windows .exe is built with wine. For windows build and test 32bit wine is required (WINEARCH=win32 during first run). Also dos2unix utility is needed for win32 tests. 

### Setup

	sudo apt-get install python pip
	sudo pip install rdflib
    git clone https://github.com/burbilog/scrapbook2zotero.git
	cd scrapbook2zotero
	./scrapbook2zotero.py ...

### Building windows .exe under Linux

Download latest python 2.7 for windows from https://www.python.org/downloads/windows/ and then

    wine msiexec /i python-2.7.14.msi /L*v log.txt
	wine pip install rdflib pyinstaller
	make win32

### Running tests

Note that regression tests requre linux to windows cross compilation setup, so build windows executable first, then run tests: 

    make win32
    make test

## TODO

Currently there is no export for 'note' or 'notex' item types. I never used notes, so my 1400+ scrapbook entries contain no notes and I can't debug them. If somebody needs export of their notes, please contact me.

## Author

* **Roman V. Isaev** - [burbilog](https://github.com/burbilog) - <rm@isaeff.net>

## Acknowledgments

Scrapbook2zotero is loosely based on (https://bitbucket.org/himselfv/scraptools/src/default/)

## License

Licensed under the [MIT License](LICENSE.txt).

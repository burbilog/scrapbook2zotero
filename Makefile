
all: 
	@echo Available targets:
	@echo
	@echo "  test - run pytest"
	@echo "  lint - run lint"
	@echo "  clean - clean everything, including windows build"
	@echo "  w - git commit"
	@echo "  win32 - build win32 executable"
	@echo "  build_samples - rebuild samples in samples/ directory (used for testing), make sure your .rdf output is correct!"

test:
	pytest

lint: lint_test lint_util

lint_test:
	python2 /usr/local/bin/pylint test_s2z.py

lint_util:
	python2 /usr/local/bin/pylint scrapbook2zotero.py

clean:
	rm -rf __pycache__
	rm -f *.pyc
	rm -rf dist
	rm -rf build
	rm -f scrapbook2zotero.spec
	rm -rf .pytest_cache
	rm -f tmp/*.rdf

w:
	git commit -a -m "working..."

win32: build32 zip32

build32:
	wine pyinstaller --onefile scrapbook2zotero.py

zip32:
	VERSION=`./get-version.sh`
	cd dist && zip scrapbook2zotero-v$(VERSION).zip scrapbook2zotero.exe


# Run this if you are sure that scrapbook2zotero output is correct
# pytest tests depend on samples/*.rdf files
build_samples:
	./scrapbook2zotero.py scrapbook_test_data samples/standard.rdf
	./scrapbook2zotero.py scrapbook_test_data samples/standard_1_4_excluded.rdf --exclude 1 4
	./scrapbook2zotero.py scrapbook_test_data samples/standard-no-collections.rdf --nocoll
	./scrapbook2zotero.py scrapbook_test_data samples/standard-no-tags.rdf --notags
	./scrapbook2zotero.py scrapbook_test_data samples/standard-no-dedup.rdf --nodedup

current-version:
	@echo Current version is `./get-version.sh`

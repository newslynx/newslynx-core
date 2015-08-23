all:
	
	make clean
	make install 
	make all_tests 
	make all_docs

clean:

	rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;

install:

	pip install .

all_tests:

	nosetests --exe

register:

	python setup.py register

distribute:

	python setup.py sdist bdist_wininst upload

sous_chef_docs:

	echo '\nSous Chefs\n-------------\n**{{ slug }}** provides access to the following Sous Chefs\n' > docs/sous-chefs.rst
	newslynx sc-docs {{ name }} -f rst >> docs/sous-chefs.rst

readme:

	pandoc README.md -t rst > docs/index.rst
	echo '\nContents\n--------\n.. toctree::\n\t:maxdepth: 2\n\n\tindex\n\tsous-chefs' >> docs/index.rst

all_docs:

	make readme
	make sous_chef_docs
	cd docs && make html

view_docs:

	cd docs/_build/html && python -m SimpleHTTPServer
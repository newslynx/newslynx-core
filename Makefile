all:
	
	make clean
	make install 
	make all_tests 
	make all_docs

clean:

	rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;

install:

	pip install .

install_dev:

	pip install --editable .

register:

	python setup.py register

distribute:

	python setup.py sdist bdist_wininst upload
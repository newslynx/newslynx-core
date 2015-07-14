clean:

	rm -rf build/ dist/ *.egg-info *.DS_Store
	rm newslynx/*.pyc newslynx/*/*.pyc newslynx/*/*/*.pyc

build:
	
	python setup.py install

defaults:

	cp newslynx/dot_newslynx/defaults/* ~/.newslynx/defaults/

documentation:
	sphinx-build -b html docs/ docs/_build/html

view_documentation:
	cd docs/_build/html && python -m SimpleHTTPServer



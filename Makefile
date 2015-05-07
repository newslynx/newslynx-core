clean:

	rm -rf build/ dist/ *.egg-info *.DS_Store
	rm newslynx/*.pyc newslynx/*/*.pyc newslynx/*/*/*.pyc

build:
	
	python setup.py install

documentation:
	sphinx-build -b html docs/ docs/_build/html

view_documentation:
	cd docs/_build/html && python -m SimpleHTTPServer




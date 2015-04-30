clean:

	rm -rf build/ dist/ *.egg-info *.DS_Store
	rm newslynx/*.pyc newslynx/*/*.pyc newslynx/*/*/*.pyc


build:
	
	python setup.py install



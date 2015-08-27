clean:

	rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;

clean_sc:

	rm -rf *.egg-info build dist && find ~/.newslynx/sous-chefs -name "*.pyc" -exec rm -rf {} \;

app_install:

	-make clean
	-pip uninstall --yes newslynx 
	-mkdir ~/.newslynx
	sleep 1
	-mkdir ~/.newslynx/sous-chefs
	sleep 1
	pip install .
	newslynx init --empty
	-make clean_sc
	sleep 2
	cat newslynx/app/sous-chefs | xargs newslynx sc-install --dev
	newslynx init

bare_install:

	-make clean
	-pip uninstall --yes newslynx 
	pip install .
	newslynx init --bare

all_tests:

	-rm -rf ~/.newslynx
	-dropdb newslynx 
	sleep 2
	-createdb newslynx
	sleep 2
	make app_install 

register:

	python setup.py register

distribute:

	python setup.py sdist bdist_wininst upload
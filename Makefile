clean:

	rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;

clean_sc:

	rm -rf *.egg-info build dist && find ~/.newslynx/sous-chefs -name "*.pyc" -exec rm -rf {} \;

app_install:

	-make clean > /dev/null
	-pip uninstall --yes newslynx 
	-mkdir ~/.newslynx > /dev/null
	sleep 1 > /dev/null > /dev/null
	-mkdir ~/.newslynx/sous-chefs > /dev/null
	-mkdir ~/.newslynx/defaults > /dev/null
	sleep 1 > /dev/null > /dev/null
	sleep 1 > /dev/null
	pip install . > /dev/null
	newslynx init --empty
	-make clean_sc > /dev/null
	sleep 2 > /dev/null
	cat newslynx/app/sous-chefs.txt | xargs newslynx sc-install --dev
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
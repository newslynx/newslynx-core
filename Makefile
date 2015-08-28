clean:

	rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;

clean_sc:

	rm -rf *.egg-info build dist && find ~/.newslynx/sous-chefs -name "*.pyc" -exec rm -rf {} \;

install:

	echo "creating a fresh install of newslynx..."
	-@(make clean > /dev/null)
	-@(pip uninstall --yes newslynx 2> /dev/null  > /dev/null)
	-@(mkdir ~/.newslynx > /dev/null)
	-@(mkdir ~/.newslynx/sous-chefs > /dev/null)
	-@(mkdir ~/.newslynx/defaults > /dev/null)
	@(sleep 1 > /dev/null)
	@(pip install -q . 2> /dev/null)

app_install:

	@(make  -s install 2> /dev/null)
	@(make -s clean_sc 2> /dev/null)
	@(newslynx init --empty 2> /dev/null)
	@(cat newslynx/app/sous-chefs.txt | xargs newslynx sc-install --dev)
	@(newslynx init --dev)

bare_install:

	@(make  -s install 2> /dev/null)
	@(newslynx init --bare)

local_tests:

	-@(rm -rf ~/.newslynx)
	-@(dropdb newslynx) 
	@(sleep 2)
	-@(createdb newslynx)
	@(sleep 2)
	@(make app_install)
	@(newslynx dev gen-random-data)

register:

	python setup.py register

distribute:

	python setup.py sdist bdist_wininst upload
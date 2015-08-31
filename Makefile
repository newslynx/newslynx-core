clean:

	@(rm -rf *.egg-info build dist && find . -name "*.pyc" -exec rm -rf {} \;)

clean_sc:

	@(rm -rf *.egg-info build dist && find ~/.newslynx/sous-chefs -name "*.pyc" -exec rm -rf {} \;)

install:

	@(echo "creating a fresh install of newslynx...")
	@(make -s clean > /dev/null)
	@(pip uninstall --yes newslynx 2> /dev/null > /dev/null; true)
	@(mkdir ~/.newslynx 2> /dev/null; true)
	@(mkdir ~/.newslynx/sous-chefs 2> /dev/null; true)
	@(mkdir ~/.newslynx/defaults 2> /dev/null; true)
	@(sleep 1 > /dev/null; true)
	@(pip install . -q 2> /dev/null; true)

app_install:

	@(make install)
	@(make clean_sc)
	@(newslynx init --empty)
	@(cat newslynx/app/sous-chefs.txt | xargs newslynx sc-install --dev)
	@(newslynx init --dev)

bare_install:

	@(make  -s install 2> /dev/null)
	@(newslynx init --bare)

test_install:

	rm -rf ~/.newslynx)
	dropdb newslynx) 
	@(sleep 2)
	createdb newslynx)
	@(sleep 2)
	@(make app_install)
	@(pip install -r test-requirements.txt -q 2> /dev/null)

register:

	@(python setup.py register)

distribute:

	@(echo "Distributing version")
	@(cat VERSION)
	@(echo "To PyPI")
	@(python setup.py sdist bdist_wininst upload)

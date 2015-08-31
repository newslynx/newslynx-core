[![Build status](https://travis-ci.org/{{ github_user }}/{{ slug }}.svg)](https://travis-ci.org/{{ github_user }}/{{ slug }}) [![Documentation Status](https://readthedocs.org/projects/{{ slug }}/badge/?version=latest)](https://readthedocs.org/projects/{{ slug }}/?badge=latest)

{{ slug }}
==========================================================================================

{{ description }}

## Installation

### Production

To install `{{ slug }}` for an active installation of `newslynx-core`, run the following command:

```bash
$ newslynx sc-install https://github.com/{{ github_user }}/{{ slug }}.git
```

To add `{{ slug }}` all orgnaizations, run:

```bash
$ newslynx sc-sync
```

### Development 

If you want to modify / add Sous Chefs to `{{ slug }}`, do the following:

**NOTE** Will install a fresh version of `newslynx` via `pip`.

```bash
$ git clone https://github.com/{{ github_user }}/{{ slug }}.git
$ cd {{ slug }}
$ pip install --editable .
```

You should now be able to run `{{ slug }}`'s Sous Chefs in development mode

```bash 
% newslynx sc-run {{ name }}/say_my_name.yaml --myname='Brian Abelson'
```

## Tests

Requires `nose`

```bash
$ make all_tests
```

## Documentation

Documentation for `{{ slug }}` is hosted on [Read The Docs](http://{{ slug }}.readthedocs.org/).

It's generated via the following steps

* converts this file (`README.md`) into a ReStructured Text file, saving it to [docs/index.rst](https://github.com/{{ github_user}}/{{ slug }}/blob/master/docs/index.rst)
* runs `newslynx sc-docs {{name}} -f rst` to generate documentation for all the Sous Chefs in `{{ slug }}` and saves the output to [docs/sous-chefs.rst](https://github.com/{{ github_user}}/{{ slug }}/blob/master/docs/sous-chefs.rst)
* Builds Sphinx Documentation from these files.


## Continuous Integration

Builds for `{{ slug }}` can be found on [Travis](https://travis-ci.org/{{ github_user }}/{{ slug }})

## Contributing

See the [contributing guidelines](https://github.com/{{ github_user}}/{{ slug }}/blob/master/CONTRIBUTING.md).


## What's in this module ?

- [README.md](https://github.com/{{ github_user}}/{{ slug }}/blob/master/README.md)
	* This file 

- [VERSION](https://github.com/{{ github_user}}/{{ slug }}/blob/master/VERSION)
	* `{{ slug }}`'s source-of-truth version.

- [requirements.txt](https://github.com/{{ github_user}}/{{ slug }}/blob/master/requirements.txt)
	* `{{ slug }}`'s python dependencies.

- [MANIFEST.in](https://github.com/{{ github_user}}/{{ slug }}/blob/master/MANIFEST.in)
	* Specifications for which files to include in the PyPI distribution.
	* See the docs on this [here](https://docs.python.org/2/distutils/sourcedist.html#specifying-the-files-to-distribute).

- [setup.py](https://github.com/{{ github_user}}/{{ slug }}/blob/master/setup.py)
	* Specification's for building `{{ slug }}`'s PyPI distribution.

- [.travis.yml](https://github.com/{{ github_user}}/{{ slug }}/blob/master/.travis.yml)
	* Configurations for Travis Continuous Integration
	* You must activate this project on [travis-ci.org](https://github.com/{{ github_user}}/{{ slug }}/blob/master/http://travis-ci.org/) for this to run on subsequent updates.

- [Makefile](https://github.com/{{ github_user}}/{{ slug }}/blob/master/Makefile)
	* Helpers for managing `{{ slug }}`.
	* Includes:
		- `make clean`: 
			* Cleans out cruft from this directory.
		- `make install`: 
			* Installs `{{ slug }}`. Assumes that you're in a virtual environment.
		- `make all_tests`: 
			* Runs the tests.
		- `make readme`
			* Converts this file to `.rst`, including a table of contents, and saves it to [docs/index.rst](https://github.com/{{ github_user}}/{{ slug }}/blob/master/docs/index.rst)
		- `make sous_chef_docs`
			* Programmtically generates [Sous Chef documentation](https://github.com/{{ github_user}}/{{ slug }}/blob/master/docs/sous-chefs.rst) by running `newslynx sc-docs {{ name}}/ --format=rst > docs/sous-chefs.rst`.
		- `make all_docs`: 
			* Builds the sphinx docs for `{{ slug }}` by running the above two commands.
		- `make view_docs`
			* Serves documentation at [localhost:8000](http://localhost:8000)
		- `make register`: 
			* Registers `{{ slug }}` on [PyPI](https://pypi.python.org/pypi).
		- `make distribute`: 
			* Publishes a new version of `{{ slug }}` to PyPI.

- [CONTRIBUTING.md](https://github.com/{{ github_user}}/{{ slug }}/blob/master/CONTRIBUTING.md)

- [{{ name }}](https://github.com/{{ github_user}}/{{ slug }}/blob/master/{{ name }}/)
	* `{{ slug }}`'s source code and Sous Chef configuration files.

- [docs](https://github.com/{{ github_user}}/{{ slug }}/blob/master/docs/)
	* Sphnix documentation for `{{ slug }}`

- [tests](https://github.com/{{ github_user}}/{{ slug }}/blob/master/tests/)
	* `nose` tests for `{{ slug }}`



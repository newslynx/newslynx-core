import os
from setuptools import setup, find_packages

README = os.path.join(os.path.dirname(__file__), 'README.md')

REQUIREMENTS = os.path.join(os.path.dirname(__file__), 'requirements.txt')
REQUIREMENTS = open(REQUIREMENTS, 'r').read().splitlines()

VERSION = os.path.join(os.path.dirname(__file__), 'VERSION')
VERSION = open(VERSION, 'r').read().strip()

PACKAGE_DATA = [
    'sql/*.sql',
    'models/*.yaml',
    'sc/*/*.yaml',
    'views/auth/templates/*.html',
    'views/api/templates/*.html',
    'sc/template/*.md',
    'sc/template/*.in',
    'sc/template/*.py',
    'sc/template/*.txt',
    'sc/template/VERSION',
    'sc/template/*.yml',
    'sc/template/.gitignore',
    'sc/template/tests/*.py',
    'sc/template/tests/fixtures/.gitkeep',
    'sc/template/docs/*.rst',
    'sc/template/docs/*.py',
    'sc/template/docs/Makefile',
    'sc/template/docs/_static/.gitkeep'
]

try:
    from newslynx.lib import doc
    long_description = doc.convert(open(README).read(), 'md', 'rst')
except:
    long_description = ""


setup(
    name='newslynx',
    version=VERSION,
    description="A modular toolkit for analytics.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='journalism analytics google-analytics twitter facebook metrics',
    author='Brian Abelson',
    author_email='brian@newslynx.org',
    url='http://newslynx.org',
    license='CCSA-4.0',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['newslynx'],
    package_data={'newslynx': PACKAGE_DATA},
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    tests_require=['nose'],
    entry_points={
        'console_scripts': [
            'newslynx = newslynx.cli:run',
            'nlx = newslynx.cli:run'
        ]
    },
)

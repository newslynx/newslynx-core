from setuptools import setup, find_packages
import os

# hack for working with pandocs on windows
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    utf8 = codecs.lookup('utf-8')
    func = lambda name, enc=utf8: {True: enc}.get(name == 'mbcs')
    codecs.register(func)

# install readme
README = os.path.join(os.path.dirname(__file__), 'README.md')

try:
    from newslynx.lib import doc
    long_description = doc.convert(open(README).read(), 'md', 'rst')
except:
    long_description = ""

REQUIREMENTS = os.path.join(os.path.dirname(__file__), 'requirements.txt')
REQUIREMENTS = open(REQUIREMENTS, 'r').read().splitlines()

VERSION = os.path.join(os.path.dirname(__file__), 'VERSION')
VERSION = open(VERSION, 'r').read().strip()

# setup
setup(
    name='{{ slug }}',
    version=VERSION,
    description='{{ description }}',
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='',
    author='{{ author }}',
    author_email='{{ email }}',
    url='http://github.com/{{ github_user }}/{{ slug }}',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    package_data={"{{ name }}": ['*.yaml']},
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    tests_require=[]
)

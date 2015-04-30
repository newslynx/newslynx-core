import os
from setuptools import setup, find_packages

README = os.path.join(os.path.dirname(__file__), 'README.md')

REQUIREMENTS = os.path.join(os.path.dirname(__file__), 'requirements.txt')
REQUIREMENTS = open(REQUIREMENTS, 'r').read().splitlines()

VERSION = os.path.join(os.path.dirname(__file__), 'VERSION')
VERSION = open(VERSION, 'r').read().strip()

setup(
    name='newslynx',
    version=VERSION,
    description="A modular toolkit for analytics.",
    long_description=open(README, 'r').read(),
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
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['newslynx'],
    package_data={},
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'newslynx = newslynx.cli:run',
        ]
    },
    tests_require=[]
)

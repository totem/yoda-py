from setuptools import setup
import sys


if not sys.version_info[0] != 3:
    print("Sorry, Python 3 is required")
    exit()

with open('./requirements.txt') as reqs_txt:
    requirements = [line for line in reqs_txt]

setup(
    name="docker-py",
    version="0.0.1",
    description="Python client for Docker.",
    author='Sukrit Khera',
    packages=['yoda'],
    install_requires=requirements,
    zip_safe=True,
    test_suite='tests',
    classifiers=[
        'Development Status :: In development',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
        'License :: The MIT License (MIT)',
        ],
    )
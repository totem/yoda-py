from setuptools import setup

with open('./requirements.txt') as reqs_txt:
    requirements = [line for line in reqs_txt]

setup(
    name="yoda-py",
    version="0.1.5",
    description="Python client for Yoda.",
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

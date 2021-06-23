import os
from setuptools import setup, find_packages


version = "0.1"

install_requires = [
    'horseman',
]

test_requires = [
    'WebTest',
    'pytest',
    'frozendict',
]

setup(
    name='reiter.view',
    version=version,
    author='Souheil CHELFOUH',
    author_email='trollfot@gmail.com',
    description='View implementation for Horseman',
    long_description=(
        open("README.txt").read() + "\n" +
        open(os.path.join("docs", "HISTORY.txt")).read()
    ),
    license='ZPL',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python:: 3 :: Only',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['reiter',],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
    },
)

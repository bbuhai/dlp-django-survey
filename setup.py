import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

dependencies = (
    'factory-boy==2.4.1'
)

setup(
    name='django_survey',
    version='0.1dev',
    license='BSD',
    author='Bogdan Buhai',
    description='A simple django app for surveys.',
    long_description=README,
    packages=find_packages(),
    install_requires=dependencies,
    include_package_data=True,  # what does this do?
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers'
    ]
)
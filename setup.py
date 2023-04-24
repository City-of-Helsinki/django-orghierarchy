import os

from setuptools import find_packages, setup

from django_orghierarchy import __version__

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-orghierarchy",
    version=__version__,
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    license="MIT License",
    description="Reusable Django application for hierarchical organizations.",
    long_description=README,
    url="https://github.com/City-of-Helsinki/django-orghierarchy",
    author="City of Helsinki",
    author_email="dev@hel.fi",
    python_requires=">=3.6",
    install_requires=[
        "Django>=2.2,<4",
        "django-mptt",
        "djangorestframework",
        "requests",
        "swapper",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)

import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-orghierarchy",
    version="0.5.1",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    license="MIT License",
    description="Reusable Django application for hierarchical organizations.",
    long_description=README,
    url="https://github.com/City-of-Helsinki/django-orghierarchy",
    author="City of Helsinki",
    author_email="dev@hel.fi",
    python_requires=">=3.9",
    install_requires=[
        "Django>=4.2,<5",
        "django-mptt",
        "djangorestframework",
        "requests",
        "swapper",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)

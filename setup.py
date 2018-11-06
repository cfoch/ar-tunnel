from setuptools import setup, find_packages


setup(
    name = "ar_tunnel",
    version = "0.1",
    keywords = "ar tunnel",
    url="https://github.com/pitivi/pitivi_echonest_extension",
    author_email = "cfoch.fabian@gmail.com",
    license = "LGPL",
    description = "An API for ArqueoPUCP",
    author = "Fabian Orccon",
    scripts = ["ar-tunnel"],
    packages = find_packages(),
    dependency_links = [],
    install_requires = [
        "flask",
        "flask_pymongo",
        "flask_restplus",
        "validate_email"
    ]
)

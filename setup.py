import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="api_factory",
    version="0.1.13",
    author="SmartXpo Solutions Limited",
    author_email="info@smartxpo.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smartxpo-solutions/api-factory",
    packages=setuptools.find_packages(),
    license='MIT License',
    classifiers=(
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    keywords='AWS Lambda functions'
)

from setuptools import setup, find_namespace_packages
setup(

    name="node-expressions",
    version="0.1.2",
    author="Oliver Batchelor",
    author_email="saulzar@gmail.com",
    description="API for using expressions to create node graphs in blender",
    url="https://github.com/saulzar/node_expressions",
    packages=find_namespace_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = [
        "fuzzywuzzy"
    ],
    python_requires='>=3.7',
)

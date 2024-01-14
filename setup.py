from setuptools import setup, find_packages

setup(
    name='PyTater',
    version='4.2.0',
    author='Adam Dean',
    author_email='adam@crypto2099.io',
    description='A Pythonic miner for STARCH CHAIN ($STRCH), the first tater-based blockchain.',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
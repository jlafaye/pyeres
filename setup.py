from setuptools import setup

setup(
    name='eres',
    version='1.0',
    description='Python module to manipulate data from ERES portfolio',
    author='Julien Lafaye',
    author_email='jlafaye@gmail.com',
    packages=['eres'],
    install_requires=['pandas'],
    entry_points={
        'console_scripts': [
            'eres-cli = eres.cli:run'
        ]
    }
)

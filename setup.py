import os

from setuptools import setup, find_packages

from pydefect import __version__

cmdclass = {}
ext_modules = []

module_dir = os.path.dirname(os.path.abspath(__file__))
reqs_raw = open(os.path.join(module_dir, "requirements.txt")).read()
reqs_list = [r.replace("==", "~=") for r in reqs_raw.split("\n")]

#with open("README.md", "r") as fh:
#    long_description = fh.read()

setup(
    name='pydefect',
    version=__version__,
    author='Yu Kumagai',
    author_email='yuuukuma@gmail.com',
    url='https://github.com/kumagai-group/pydefect',
    packages=find_packages(),
    license='MIT license',
    description="Integrated environment for first-principles point-defect "
                "calculations using vasp",
    classifiers=[
        'Programming Language :: Python :: 3.6',
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=reqs_list,
    cmdclass=cmdclass,
    ext_modules=ext_modules,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pydefect = pydefect.cli.main:main',
        ]
    }
)

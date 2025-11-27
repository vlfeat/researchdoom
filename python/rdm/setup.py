from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="researchdoom",
    version="1.0.0",
    author="Andrea Vedaldi (original), Python port contributors",
    author_email="",
    description="Python port of ResearchDoom MATLAB library for game recording analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vlfeat/researchdoom",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'rdm-test=rdm_test:main',
            'rdm-test-warp=rdm_test_warp:main',
            'cocodoom-gen=cocodoom_gen:main',
            'cocodoom-make=cocodoom_make:main',
            'cocodoom-combine=cocodoom_combine:main',
            'cocodoom-split=cocodoom_split:main',
            'cocodoom-test=cocodoom_test:main',
            'cocodoom-gallery=cocodoom_gallery:main',
        ],
    },
)

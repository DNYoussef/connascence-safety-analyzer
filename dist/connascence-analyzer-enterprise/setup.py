from setuptools import setup, find_packages

setup(
    name="connascence-analyzer-enterprise",
    version="1.0.0",
    description="Enterprise Security and Compliance Features",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Connascence Systems",
    author_email="support@connascence.com",
    url="https://connascence.com",
    packages=find_packages(),
    install_requires=['cryptography', 'pyjwt', 'ldap3', 'psycopg2'],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    entry_points={
        "console_scripts": [
            "connascence=cli.connascence:main",
        ],
    },
    package_data={
        "policy": ["presets/*.yml"],
        "grammar": ["overlays/*.yml"], 
        "reporting": ["templates/*.j2"],
    },
    include_package_data=True,
)
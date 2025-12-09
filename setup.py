from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
requirements = []
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="primbot",
    version="1.0.3",
    author="Dev-NTIC",
    description="PRIMBOT CLI - PrimLogix Debug Agent with Gemini AI and Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/carlcgb/bot-prim",
    project_urls={
        "Homepage": "https://github.com/carlcgb/bot-prim",
        "Documentation": "https://github.com/carlcgb/bot-prim#readme",
        "Issues": "https://github.com/carlcgb/bot-prim/issues",
    },
    packages=find_packages(),
    py_modules=["agent", "app", "scraper", "knowledge_base", "ingest", "primbot_cli"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "primbot=primbot_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)


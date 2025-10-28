from setuptools import setup, find_packages

setup(
    name="podcast_translator",
    version="1.0.0",
    description="Automatic podcast translator: speaker detection, Hebrew translation, TTS",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/<USERNAME>/podcast-translator",
    packages=find_packages(),
    py_modules=["podcast_translator"],
    python_requires=">=3.10",
    install_requires=[
        "google-cloud-speech>=2.20.0",
        "google-genai>=0.1.0",
        "regex>=2023.10.23",
    ],
    entry_points={
        "console_scripts": [
            "podcast-translator=podcast_translator:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)

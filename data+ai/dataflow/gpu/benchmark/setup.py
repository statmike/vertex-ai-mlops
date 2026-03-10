"""Beam packaging setup for Dataflow workers."""

from setuptools import setup, find_packages

setup(
    name="benchmark",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "apache-beam[gcp]>=2.61.0",
        "torch>=2.1.0",
        "transformers>=4.36.0",
        "google-cloud-pubsub>=2.18.0",
        "google-auth>=2.23.0",
        "requests>=2.31.0",
    ],
)

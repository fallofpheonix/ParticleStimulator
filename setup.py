from setuptools import find_packages, setup


setup(
    name="particle-stimulator",
    version="0.1.0",
    description="Particle physics simulator platform backend runtime",
    packages=find_packages(where=".", include=["src", "src.*"]),
    package_data={"src.web": ["static/*"]},
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "joblib>=1.3",
        "numpy>=1.24",
        "pandas>=2.0",
        "scikit-learn>=1.3",
        "scipy>=1.10",
        "websockets>=12",
    ],
    extras_require={
        "ml": [
            "xgboost>=2.0",
        ]
    },
)

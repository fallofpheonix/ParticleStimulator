from setuptools import find_packages, setup


setup(
    name="particle-stimulator",
    version="0.1.0",
    description="Deterministic MVP particle accelerator and collision simulator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"web": ["static/*"]},
    python_requires=">=3.11",
    extras_require={
        "ml": [
            "joblib>=1.3",
            "numpy>=1.24",
            "pandas>=2.0",
            "scikit-learn>=1.3",
            "xgboost>=2.0",
        ]
    },
)

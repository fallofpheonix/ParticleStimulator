from setuptools import find_packages, setup


setup(
    name="particle-stimulator",
    version="0.1.0",
    description="Particle physics simulator platform backend runtime",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["analysis", "analysis.*", "simulation_core", "simulation_core.*", "web", "web.*"]),
    package_data={"web": ["static/*"]},
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.24",
        "websockets>=12",
    ],
    extras_require={
        "ml": ["joblib>=1.3", "pandas>=2.0", "scikit-learn>=1.3", "xgboost>=2.0"],
        "optional": ["fastapi>=0.110.0", "h5py>=3.10", "pyarrow>=15.0", "pydantic>=2.0", "uvicorn>=0.29.0"],
    },
)

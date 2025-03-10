from setuptools import setup, find_packages

setup(
    name="iot-building-simulator",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.2",
        "psycopg2-binary>=2.9.1",
        "sqlalchemy>=1.4.23",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "python-json-logger>=2.0.2",
        "websockets>=10.0",
        "aiohttp>=3.8.0",
        "pyyaml>=5.4.1",
        "python-multipart>=0.0.5",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.0",
            "pytest-asyncio>=0.15.1",
            "black>=21.5b2",
            "flake8>=3.9.2",
            "mypy>=0.910"
        ]
    },
    author="Tu Nombre",
    author_email="tu@email.com",
    description="Simulador de dispositivos IoT para edificios",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/iot-building-simulator",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
) 
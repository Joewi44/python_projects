from setuptools import setup, find_packages


setup(
    name='ocw_project',
    version='0.1.1',
    description='OCW Systematiek for managing road components and scenarios',
    author='Uwe Versavel',
    author_email='Uwe.versavel@telenet.be',
    packages=find_packages(),  # Automatically finds all packages with __init__.py
    package_data={
        'ocw_project': ['**/*.yaml', '**/*.json'],
    },
    include_package_data=True,
    install_requires=["pandas", "geopandas", "pandas-datareader", "matplotlib", "setuptools", "panel", 
                      "fastparquet", "pyarrow", "hvplot", "folium", "pyproj", "shapely", "pyogrio", 
                      "bokeh", "tornado", "ipywidgets", "jupyter_bokeh", "pyviz_comms", "numpy", "pyinstaller"]
, 
    python_requires='>=3.12',
    entry_points={
        'console_scripts': [
            'ocw-run = ocw_project.cli:main'
        ]
    }
)

# pip install -e .
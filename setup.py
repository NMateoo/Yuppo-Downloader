from setuptools import setup, find_packages

setup(
    name='yupoo-downloader',
    version='1.0.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'requests',
        'beautifulsoup4',
        'pandas',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'yupoo-downloader=yupoo_downloader.gui:main',
        ],
    },
    description='Descarga automatizada de catálogos Yupoo.',
    author='MateoBoss',
    author_email='tu_email@example.com',
    url='https://github.com/tuusuario/yupoo-downloader',
)
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
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'yupoo-downloader=yupoo_downloader.gui:main',
        ],
    },
    description='Descarga automatizada de catálogos Yupoo.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='MateoBoss',
    author_email='nicolasmateocontacto@gmail.com',
    url='https://github.com/NMateoo/Yuppo-Downloader',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='yupoo downloader automation',
    test_suite='tests',
)

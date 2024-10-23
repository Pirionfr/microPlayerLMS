from setuptools import setup, find_packages

setup(
    name="micro_player",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiohttp",
        "gpiozero",
        "numpy",
        "pigpio",
        "pysqueezebox",
        "requests",
        "RPi.GPIO",
        "spidev",
        "websockets",
        "Pillow",
    ],
    entry_points={
        'console_scripts': [
            'mon_programme=mon_programme.main:main_function',  # Point d'entrée du programme
        ],
    },
    author="pirionfr",
    author_email="grytes29@gmail.com",
    description="e-paper lyrion client",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/microPLayer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
)

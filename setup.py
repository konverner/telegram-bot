from setuptools import setup, find_packages

setup(
    name="telegram_bot",
    version='0.1.0',
    description='',
    author='Konstantin VERNER',
    author_email='konst.verner@gmail.com',
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "pyTelegramBotAPI",
        "fake_useragent",
        "selenium"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
)
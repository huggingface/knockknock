from setuptools import setup, find_packages
from io import open

setup(
    name='knockknock',
    version='0.1.3',
    description='Be notified when your training is complete with only two additional lines of code',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='http://github.com/huggingface/knockknock',
    author='Victor SANH',
    author_email='victorsanh@gmail.com',
    license='MIT',
    packages=find_packages(),
        entry_points={
            'console_scripts': [
                'knockknock = knockknock.__main__:main'
            ]
    },
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=[
        'yagmail>=0.11.214',
        'keyring',
        'python-telegram-bot',
        'requests'
    ],
    classifiers=[
        'Intended Audience :: Science/Research',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ]
)

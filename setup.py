from setuptools import setup, find_packages

setup(
	name='knockknock',
	version='0.1',
	description='Be notified when your training is finished with only two additional lines of code',
	url='http://github.com/huggingface/knockknock',
	author='Victor SANH',
	author_email='victorsanh@gmail.com',
	license='MIT',
	packages=find_packages(),
	zip_safe=False,
	python_requires='>=3.6',
	install_requires=[
		'yagmail>=0.11.214',
		'keyring',
		'python-telegram-bot'
	]
)

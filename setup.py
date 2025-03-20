from setuptools import setup, find_packages


setup(
    name='text_formatter',
    version="0.0.17",
    # url='none',
    # author='',
    # author_email='x@x.com',
    py_modules=['text_formatter'],
    install_requires=[
        'markdown',
        'markdownify',
        'bs4',
        'bbcode',
        'nh3'
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
)
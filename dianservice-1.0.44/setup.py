import setuptools
from sys import version

if version < '2.2.3':
	from distutils.dist import DistributionMetadata
	DistributionMetadata.classifiers = None
	DistributionMetadata.download_url = None
	
from distutils.core import setup

setuptools.setup(
                    name='dianservice',
                    version='1.0.44',
                    author='@rockscripts',
                    author_email='rockscripts@gmail.com',
                    description='DIAN - sign and verify xml',
                    long_description="Generate signatures for Dian e-documents",
                    install_requires=[
                                        'lxml >= 4.2.5',
                                        'xmlsec >= 1.3.3'
                                     ],
                    platforms='any',
                    url='https://instagram.com/rockscripts/',
                    packages=['dianservice'],
                    python_requires='>=2.7.*',
                )

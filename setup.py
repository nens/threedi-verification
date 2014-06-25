from setuptools import setup

version = '0.3.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django >= 1.6',
    'Jinja2',
    'django-debug-toolbar',
    'django-extensions',
    'django-jsonfield',
    'gunicorn',
    'ipdb',
    'netCDF4',
    'setuptools',
    'south',
    ],

tests_require = [
    'nose',
    'mock',
    'django-nose',
    'coverage',
    ]

setup(name='threedi-verification',
      version=version,
      description="3Di test cases verification tool",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Reinout van Rees',
      author_email='reinout.vanrees@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['threedi_verification'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
              'verify = threedi_verification.verification:main',
          ]},
      )

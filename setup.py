import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
    ],
}

TESTS_REQUIRE = [
    'fakeredis',
    'fudge',
    'nose',
    'nti.testing',
    'zope.dottedname',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.store',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI Store",
    long_description=(_read('README.rst') + '\n\n' + _read("CHANGES.rst")),
    license='Apache',
    keywords='store purchase',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    url="https://github.com/NextThought/nti.store",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'BTrees',
        'nti.base',
        'nti.containers',
        'nti.contentfragments',
        'nti.coremetadata',
	    'nti.dataserver',
        'nti.dublincore',
        'nti.externalization',
	    'nti.invitations',
        'nti.mimetype',
        'nti.namedfile',
        'nti.ntiids',
        'nti.property',
        'nti.schema',
        'nti.site',
        'nti.zope_catalog',
        'persistent',
        'requests',
        'simplejson',
        'six',
        'stripe',
        'z3c.schema',
        'ZODB',
        'zope.annotation',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.configuration',
        'zope.container',
        'zope.deprecation',
        'zope.event',
        'zope.generations',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.location',
        'zope.mimetype',
        'zope.schema',
        'zope.security',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)

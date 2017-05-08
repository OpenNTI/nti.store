#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary.interfaces import IContentPackageLibrary


def get_library(library=None):
    if library is None:
        return component.queryUtility(IContentPackageLibrary)
    return library


def get_paths(ntiid, library=None):
    library = get_library()
    paths = library.pathToNTIID(ntiid) if library and ntiid else ()
    return paths or ()


def get_ntiid_path(ntiid, library=None):
    result = get_paths(ntiid, library)
    result = tuple(p.ntiid for p in result) if result else ()
    return result


def get_collection_root(ntiid, library=None):
    paths = get_paths(ntiid, library)
    return paths[0] if paths else None


def get_collection_root_ntiid(ntiid, library=None):
    root = get_collection_root(ntiid, library)
    result = root.ntiid if root is not None else None
    return result

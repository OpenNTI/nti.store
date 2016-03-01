#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary.interfaces import IContentPackageLibrary

def get_library(library=None, registry=component):
	if library is None:
		return registry.queryUtility(IContentPackageLibrary)
	return library

def get_paths(ntiid, library=None, registry=component):
	library = get_library(registry=registry)
	paths = library.pathToNTIID(ntiid) if library and ntiid else ()
	return paths or ()

def get_ntiid_path(ntiid, library=None, registry=component):
	result = get_paths(ntiid, library, registry)
	result = tuple(p.ntiid for p in result) if result else ()
	return result

def get_collection_root(ntiid, library=None, registry=component):
	paths = get_paths(ntiid, library, registry)
	return paths[0] if paths else None

def get_collection_root_ntiid(ntiid, library=None, registry=component):
	root = get_collection_root(ntiid, library, registry)
	result = root.ntiid if root is not None else None
	return result

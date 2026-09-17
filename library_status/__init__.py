#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre Interface Action wrapper for YES24 Library Status."""

from calibre.customize import InterfaceActionBase


class Yes24LibraryStatusPlugin(InterfaceActionBase):
    name = "YES24 Library Status"
    description = (
        "Record YES24 bestseller, steady-seller, and ranking history in Calibre "
        "custom columns. After Calibre starts, this plugin automatically connects "
        "to the YES24 Open API to prefetch public ranking lists and refreshes a "
        "local cache of product IDs exposed by the YES24 domestic steady-seller "
        "storefront page. It does not upload EPUB files or your library metadata."
    )
    supported_platforms = ["windows", "osx", "linux"]
    author = "xixsxix"
    version = (0, 3, 7)
    minimum_calibre_version = (9, 0, 0)
    actual_plugin = (
        "calibre_plugins.yes24_library_status.ui_036:"
        "Yes24LibraryStatusAction036"
    )

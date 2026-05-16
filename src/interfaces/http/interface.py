"""
HTTP Interface (mirrors basecode-golang interfaces/http/interface.go).
"""

from definitions.applications.app import AppContext


class HttpInterface:
    def __init__(self, app_context: AppContext):
        self.app_context = app_context

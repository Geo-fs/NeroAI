from __future__ import annotations

from app.plugins.file_read import FileReadPlugin
from app.plugins.file_read_batch import FileReadBatchPlugin
from app.plugins.file_list import FileListPlugin
from app.plugins.file_write import FileWritePlugin
from app.services.plugins_local import load_local_plugins

PLUGIN_REGISTRY = {
    "file_read": FileReadPlugin(),
    "file_write": FileWritePlugin(),
    "file_list": FileListPlugin(),
    "file_read_batch": FileReadBatchPlugin(),
}

try:
    PLUGIN_REGISTRY.update(load_local_plugins())
except Exception:
    pass

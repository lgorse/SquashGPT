"""
Workaround for missing tkinter in mouseinfo module.
This patches mouseinfo to avoid importing tkinter which we don't actually need.
"""
import sys
from unittest.mock import MagicMock

# Create fake tkinter modules before mouseinfo tries to import them
sys.modules['tkinter'] = MagicMock()
sys.modules['_tkinter'] = MagicMock()

print("✓ Tkinter import patched successfully")

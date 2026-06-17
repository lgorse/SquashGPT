"""
Workaround for missing tkinter in mouseinfo module.
This patches mouseinfo to avoid importing tkinter which we don't actually need.
"""
import sys
from unittest.mock import MagicMock

# Create a mock tkinter module with necessary attributes
class MockTk:
    TkVersion = 8.6  # Set version to satisfy pymsgbox check
    def __init__(self, *args, **kwargs):
        pass
    def withdraw(self):
        pass
    def update(self):
        pass
    def destroy(self):
        pass

mock_tkinter = MagicMock()
mock_tkinter.Tk = MockTk
mock_tkinter.TkVersion = 8.6

# Patch both tkinter modules
sys.modules['tkinter'] = mock_tkinter
sys.modules['_tkinter'] = MagicMock()

print("✓ Tkinter import patched successfully")

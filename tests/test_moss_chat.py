"""MOSS contextual identity and local chat journal regression tests."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))

from chat_store import ChatStore
from moss_context import system_context


class ContextTests(unittest.TestCase):
    def test_transparent_model_identity(self):
        prompt = system_context("qwen2.5:1.5b", "engineering")
        self.assertIn("MOSS/KYVRAEL", prompt)
        self.assertIn("qwen2.5:1.5b", prompt)
        self.assertIn("não tens ferramentas", prompt)
        self.assertIn("GENESIS X", prompt)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            system_context("phi3:latest", "dangerous")


class StoreTests(unittest.TestCase):
    def test_history_context_and_clear(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ChatStore(Path(folder) / "chat.sqlite3")
            store.append_exchange("First user", "First assistant", model="phi3", mode="general")
            store.append_exchange("Second user", "Second assistant", model="phi3", mode="general")
            self.assertEqual([x["role"] for x in store.history()],
                             ["user", "assistant", "user", "assistant"])
            self.assertEqual([x["role"] for x in store.context()],
                             ["user", "assistant", "user", "assistant"])
            store.clear()
            self.assertEqual(store.history(), [])

    def test_context_keeps_complete_pairs(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ChatStore(Path(folder) / "chat.sqlite3")
            store.append_exchange("Long request " + "x" * 2500,
                                  "Long answer " + "y" * 2500, model="phi3", mode="general")
            store.append_exchange("Recent", "Recent reply", model="phi3", mode="general")
            recent = store.context(char_budget=600)
            self.assertEqual([item["content"] for item in recent], ["Recent", "Recent reply"])

    def test_message_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ChatStore(Path(folder) / "chat.sqlite3")
            with self.assertRaises(ValueError):
                store.append_exchange("", "Response", model="phi3", mode="general")


if __name__ == "__main__":
    unittest.main()

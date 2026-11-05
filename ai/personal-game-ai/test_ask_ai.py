import io
import json
import unittest
from unittest.mock import patch

import ask_ai


class AskAiTests(unittest.TestCase):
    def test_default_request_uses_gemma_and_4096_output_tokens(self):
        response = io.BytesIO(json.dumps({
            "done_reason": "stop",
            "message": {"content": '{"ok": true}'},
        }).encode("utf-8"))

        with patch.object(ask_ai, "urlopen", return_value=response) as urlopen:
            answer = ask_ai.ask_model("테스트 요청")

        request = urlopen.call_args.args[0]
        data = json.loads(request.data.decode("utf-8"))
        self.assertEqual(data["model"], "gemma4:26b")
        self.assertEqual(data["options"]["num_predict"], 4096)
        self.assertEqual(data["messages"][-1]["content"], "테스트 요청")
        self.assertEqual(answer, '{"ok": true}')

    def test_length_limited_response_is_rejected(self):
        response = io.BytesIO(json.dumps({
            "done_reason": "length",
            "message": {"content": "partial"},
        }).encode("utf-8"))

        with patch.object(ask_ai, "urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "길이 제한"):
                ask_ai.ask_model("긴 요청")


if __name__ == "__main__":
    unittest.main()

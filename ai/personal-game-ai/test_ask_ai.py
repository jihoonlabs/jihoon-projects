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
        self.assertIs(data["think"], False)
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


class ParseJsonAnswerTests(unittest.TestCase):
    def test_plain_and_whole_fenced_json_are_accepted(self):
        for answer in (
            '{"a": 1}',
            '  {"a": 1}\n',
            '```json\n{"a": 1}\n```',
            '```JSON\n{"a": 1}\n```',
            '```\n{"a": 1}\n```',
            '\n```json  \r\n{"a": 1}\r\n```\n',
        ):
            with self.subTest(answer=answer):
                self.assertEqual(ask_ai.parse_json_answer(answer), {"a": 1})

    def test_backticks_inside_json_string_are_kept(self):
        answer = '```json\n{"code": "x = \\"```\\""}\n```'
        self.assertEqual(
            ask_ai.parse_json_answer(answer), {"code": 'x = "```"'}
        )

    def test_other_shapes_are_rejected(self):
        for answer in (
            'Here:\n```json\n{"a": 1}\n```',
            '```json\n{"a": 1}\n```\nDone.',
            '```json\n{"a": 1}\n```\n```json\n{"b": 2}\n```',
            '```json\n{"a": 1}',
            '```python\n{"a": 1}\n```',
            '```json {"a": 1}```',
            '',
            'invalid',
        ):
            with self.subTest(answer=answer):
                with self.assertRaises(ValueError):
                    ask_ai.parse_json_answer(answer)

    def test_non_string_is_rejected(self):
        with self.assertRaises(ValueError):
            ask_ai.parse_json_answer(None)


if __name__ == "__main__":
    unittest.main()

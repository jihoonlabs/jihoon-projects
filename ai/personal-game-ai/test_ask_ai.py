import copy
import io
import json
import os
import unittest
from unittest.mock import patch

import ask_ai


class AskAiTests(unittest.TestCase):
    def test_environment_options_are_per_call_and_do_not_mutate_defaults(self):
        before = copy.deepcopy(ask_ai.payload)
        response = {"done_reason": "stop", "message": {"content": "ok"}}
        with patch.dict(os.environ, {"GAME_AI_NUM_CTX": "16384", "GAME_AI_NUM_PREDICT": "6144"}, clear=True):
            with patch.object(ask_ai, "urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as api:
                self.assertEqual(ask_ai.ask_model("first"), "ok")
                sent = json.loads(api.call_args.args[0].data)
                self.assertEqual(sent["options"]["num_ctx"], 16384)
                self.assertEqual(sent["options"]["num_predict"], 6144)
                self.assertEqual(sent["messages"][-1]["content"], "first")
        self.assertEqual(ask_ai.payload, before)

    def test_invalid_limits_fail_before_http(self):
        for values in (
            {"GAME_AI_NUM_PREDICT": "bad"},
            {"GAME_AI_NUM_PREDICT": "-1"},
            {"GAME_AI_NUM_CTX": "0"},
            {"GAME_AI_NUM_CTX": "2048", "GAME_AI_NUM_PREDICT": "2048"},
        ):
            with self.subTest(values=values), patch.dict(os.environ, values, clear=True):
                with patch.object(ask_ai, "urlopen") as api:
                    with self.assertRaises(ValueError):
                        ask_ai.ask_model("prompt")
                    api.assert_not_called()

    def test_truncated_json_is_rejected_even_if_syntactically_valid(self):
        response = {"done_reason": "length", "message": {"content": "{}"}}
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(ask_ai, "urlopen", return_value=io.BytesIO(json.dumps(response).encode())):
                with self.assertRaises(ask_ai.ModelLengthError) as caught:
                    ask_ai.ask_model("prompt")
        self.assertEqual(caught.exception.result, response)

    def test_defaults_remain_compatible(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ask_ai.model_options(), ask_ai.payload["options"])


if __name__ == "__main__":
    unittest.main()

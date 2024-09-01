#!/usr/bin/env python3


from pyfyzz.models import FuzzCase


class TestCaseSerializer:
    @staticmethod
    def test_fuzzcase_serialize():
        # Create a FuzzCase instance
        fuzz_case = FuzzCase(
            inputs={"a": 1, "b": 2},
            return_value=3,
            exception=None,
            encoded_source="c29tZV9lbmNvZGVkX3NvdXJjZQ==",  # Example base64 encoded string
        )

        # serialization logic
        serialized_data = {
            "inputs": fuzz_case.inputs,
            "return_value": fuzz_case.return_value,
            "exception": fuzz_case.exception,
            "encoded_source": fuzz_case.encoded_source,
        }

        # serialization matches the expected output
        assert serialized_data == {
            "inputs": {"a": 1, "b": 2},
            "return_value": 3,
            "exception": None,
            "encoded_source": "c29tZV9lbmNvZGVkX3NvdXJjZQ==",
        }

    @staticmethod
    def test_fuzzcase_deserialize():
        # Create a dictionary that represents serialized FuzzCase data
        data = {
            "inputs": {"a": 1, "b": 2},
            "return_value": 3,
            "exception": None,
            "encoded_source": "c29tZV9lbmNvZGVkX3NvdXJjZQ==",  # Example base64 encoded string
        }

        # deserialization logic
        fuzz_case = FuzzCase(
            inputs=data["inputs"],
            return_value=data.get("return_value"),
            exception=data.get("exception"),
            encoded_source=data.get("encoded_source"),
        )

        # deserialized object matches the expected FuzzCase
        assert fuzz_case.inputs == {"a": 1, "b": 2}
        assert fuzz_case.return_value == 3
        assert fuzz_case.exception is None
        assert fuzz_case.encoded_source == "c29tZV9lbmNvZGVkX3NvdXJjZQ=="

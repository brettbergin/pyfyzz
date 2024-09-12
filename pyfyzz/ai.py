#!/usr/bin/env python3

import base64
import openai


class ChatGPTInterface:
    def __init__(self, logger, api_key: str = None, model: str = "gpt-4"):
        self.logger = logger
        self.model = model

        if api_key:
            self.api_key = api_key
            self.client = self._define_chatgpt_api_key(self.api_key)
        else:
            raise NotImplementedError("Missing OpenAI API Key.")

    def _define_chatgpt_api_key(self, key):
        openai.api_key = key
        return openai

    def suggest_improvement(self, source_code: str, code_path: str) -> str:
        """
        Submits the exception details and source code to ChatGPT to ask for code improvements.
        
        :param fuzz_case: A FuzzCase object containing details about the fuzzing test.
        :return: A suggested code improvement from ChatGPT.
        """    
        self.logger.log("info", f"[+] Making improvement request to chatgpt for: {code_path}")
        
        decoded_source = base64.b64decode(source_code).decode('utf-8')

        prompt = f"""
        The following Python code will now be known as the "original_code". 
        This code has conditions within it where Exceptions are being 
        thrown due to invalidated input into the method provided.

        {decoded_source}

        Provide a code improvement for our "original_code" that prevents the mentioned 
        exception from occurring. Make sure to make use of isinstance() and type() as a mechanism 
        to improve the "original_code". If you plan to raise an built-in exception in the handling
        of the exception, please also demonstrate a return statement thats commented out on the following line
        so the reader can weigh the options of using raise versus return.

        Make sure to only return the improved code.
        This means NO encapsulation of python code in markdown, markup, or any other content supported information.
        """

        self.logger.log("debug", f"[!] Prompt: {prompt}")

        # Make the API request to ChatGPT
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that improves Python code based on provided exception details. Only respond with code, without any explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        improved_code = response.choices[0].message.content
        self.logger.log("debug", f"[!] Improved Code: {improved_code}")

        return improved_code

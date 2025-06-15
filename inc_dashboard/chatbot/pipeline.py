# chatbot/pipeline.py

from llama_cpp import Llama
import os

class MistralChatbot:
    def __init__(self, model_path: str):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=8,
            use_mlock=True  # optional
        )

    def ask(self, prompt: str, history: list = []) -> str:
        system_prompt = "You are a helpful assistant."
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["bot"]})
        messages.append({"role": "user", "content": prompt})

        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=512,
            stop=["</s>"]
        )
        return response['choices'][0]['message']['content'].strip()
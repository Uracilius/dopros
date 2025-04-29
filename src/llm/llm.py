import os
from llama_cpp import Llama
from src.llm import config
from transformers import AutoTokenizer
import os


class LLM:

    def __init__(
        self,
        model_path=str(
            config.PATH_TO_LOCAL_LLM
        ),  # str conversion because An error occurred: 'WindowsPath' object has no attribute 'encode'
        n_ctx: int = config.MAX_CONTEXT,
    ):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"GGUF model not found: {model_path}")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=config.NUM_THREADS,
            use_mlock=False,
            use_mmap=True,
            chat_format="llama-3",
            verbose=False,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(config.HF_MODEL_NAME)

    def local_llm(self, system_prompt, user_prompt, max_tokens=config.MAX_TOKENS):
        return self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=config.TEMPERATURE,
            top_k=config.TOP_K,
            top_p=config.TOP_P,
            repeat_penalty=config.REPEAT_PENALTY,
        )["choices"][0]["message"]["content"].strip()

    def improve_transcription(
        self,
        transcription,
        prompt_path="src/llm/prompts/improve_transcription_prompt_uni.txt",
    ):
        transcription = self._smart_text_detect(transcription)
        chunks = self._break_text_into_chunks(transcription)

        with open(prompt_path, "r", encoding="utf-8") as prompt_file:
            system_prompt = prompt_file.read().strip()

        improved_chunks = []
        for chunk in chunks:
            result = self.local_llm(system_prompt, chunk, max_tokens=2048)
            improved_chunks.append(result)

        return " ".join(improved_chunks)

    def summarize(
        self, transcription, prompt_path="src/llm/prompts/summarize_prompt_uni.txt"
    ):
        transcription = self._smart_text_detect(transcription)
        chunks = self._break_text_into_chunks(transcription)

        with open(prompt_path, "r", encoding="utf-8") as prompt_file:
            system_prompt = prompt_file.read().strip()

        summary_chunks = []
        for chunk in chunks:
            result = self.local_llm(system_prompt, chunk, max_tokens=1024)
            summary_chunks.append(result)

        return " ".join(summary_chunks)

    def analyze(
        self,
        facts,
        all_facts=[],
        prompt_path="src/llm/prompts/analyze_prompt_uni.txt",
    ):
        facts = self._smart_text_detect(facts)

        with open(prompt_path, "r", encoding="utf-8") as prompt_file:
            system_prompt = prompt_file.read().strip()

        result = self.local_llm(system_prompt, facts)
        return result

    def _smart_text_detect(self, text_or_path):
        if os.path.isfile(text_or_path):
            with open(text_or_path, "r", encoding="utf-8") as file:
                return file.read()
        return text_or_path

    def _break_text_into_chunks(self, text, chunk_size=None):
        if chunk_size is None:
            chunk_size = config.MAX_CONTEXT // 8

        tokens = self.tokenizer.encode(text)
        token_chunks = [
            tokens[i : i + chunk_size] for i in range(0, len(tokens), chunk_size)
        ]

        chunks = [self.tokenizer.decode(chunk) for chunk in token_chunks]
        return chunks


if __name__ == "__main__":
    try:
        llm = LLM()
        text = llm._smart_text_detect(
            r"C:\Users\user\Desktop\work\device_prototyping\main\src\transcription\results\test_transcription.txt"
        )
        improved_text = llm.improve_transcription(text)
        print("Improved Transcription:", improved_text)
    except Exception as e:
        print(f"An error occurred: {e}")

    ######ПРЕДЫДУЩАЯ ВЕРСИЯ КОДА С LMSTUDIO SERVER, C УНИКАЛЬНЫМИ МОДЕЛЯМИ ДЛЯ КАЖДОГО ЯЗЫКА
#     def _get_kazakh_llm_response(
#         self, text, url="http://localhost:1234/v1/chat/completions"
#     ):
#         headers = {"Content-Type": "application/json; charset=utf-8"}
#         payload = {
#             "model": "checkpoints_llama8b_031224_18900",
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": "Сізге транскрипция қатесін түзету тапсырылған. Тек түзетілген нұсқаны қайтарыңыз. Қосымша түсініктеме, ескертпе, не басқа мәтін жазбаңыз.",
#                 },
#                 {"role": "user", "content": text},
#             ],
#             "max_tokens": -1,  # Control output length
#             "stop": ["\n\n", "Қосымша"],  # Stop generation if unwanted text appears
#             "temperature": 0.1,  # Reduce randomness for better consistency
#             "top_p": 0.95,
#         }

#         try:
#             response = requests.post(url, headers=headers, json=payload)
#             response.encoding = "utf-8"
#             response.encoding = "utf-8"
#             result = response.json()
#             print(result)

#             if "choices" not in result or not result["choices"]:
#                 raise LLMError("Invalid response format from Kazakh LLM")

#             return result["choices"][0]["message"].get("content", text).strip()
#         except requests.exceptions.RequestException as e:
#             raise LLMError("Kazakh LLM unreachable")

#     def _get_russian_llm_response(
#         self, text, url="http://localhost:1234/v1/chat/completions"
#     ):
#         headers = {"Content-Type": "application/json; charset=utf-8"}
#         payload = {
#             "model": "checkpoints_llama8b_031224_18900",
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": "Вам дали транскрипцию. Улучшите ее и верните исправленный вариант. ТОЛЬКО исправленный вариант, ничего больше",
#                 },
#                 {"role": "user", "content": text},
#             ],
#             "max_tokens": -1,  # Control output length
#             "stop": ["\n\n", "Қосымша"],  # Stop generation if unwanted text appears
#             "temperature": 0.1,  # Reduce randomness for better consistency
#             "top_p": 0.95,
#         }

#         try:
#             response = requests.post(url, headers=headers, json=payload)
#             response.encoding = "utf-8"
#             response.raise_for_status()
#             result = response.json()
#             print(result)

#             if "choices" not in result or not result["choices"]:
#                 raise LLMError("Invalid response format from Russian LLM")

#             return result["choices"][0]["message"].get("content", text).strip()
#         except requests.exceptions.RequestException as e:
#             raise LLMError("Russian LLM unreachable")

#     def improve_kazakh_transcription(
#         self,
#         text_or_path,
#         prompt_path="src/llm/prompts/improve_transcription_prompt_kz.txt",
#     ):
#         try:
#             transcription = self._smart_text_detect(text_or_path)

#             with open(prompt_path, "r", encoding="utf-8") as prompt_file:
#                 prompt = prompt_file.read()

#             combined_text = transcription + "\nprompt:\n" + prompt

#             improved_transcription = self._get_kazakh_llm_response(combined_text)

#             return improved_transcription
#         except Exception as e:
#             print(f"Error during improve_kazakh_transcription: {e}")
#             return None

#     def _get_llm_response(
#         self, text, url="http://localhost:1234/v1/chat/completions"
#     ):
#         headers = {"Content-Type": "application/json; charset=utf-8"}
#         payload = {
#             "model": "checkpoints_llama8b_031224_18900",
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": "Сізге транскрипция қатесін түзету тапсырылған. Тек түзетілген нұсқаны қайтарыңыз. Қосымша түсініктеме, ескертпе, не басқа мәтін жазбаңыз.",
#                 },
#                 {"role": "user", "content": text},
#             ],
#             "max_tokens": -1,  # Control output length
#             "stop": ["\n\n", "Қосымша"],  # Stop generation if unwanted text appears
#             "temperature": 0.1,  # Reduce randomness for better consistency
#             "top_p": 0.95,
#         }

#         try:
#             response = requests.post(url, headers=headers, json=payload)
#             response.encoding = "utf-8"
#             response.encoding = "utf-8"
#             result = response.json()
#             print(result)

#             if "choices" not in result or not result["choices"]:
#                 raise LLMError("Invalid response format from Kazakh LLM")

#             return result["choices"][0]["message"].get("content", text).strip()
#         except requests.exceptions.RequestException as e:
#             raise LLMError("Kazakh LLM unreachable")
# # |
# def improve_transcription(
#         self,
#         text_or_path,
#         prompt_path="src/llm/prompts/improve_transcription_prompt_uni.txt",
#     ):
#         try:
#             transcription = self._smart_text_detect(text_or_path)

#             with open(prompt_path, "r", encoding="utf-8") as prompt_file:
#                 prompt = prompt_file.read()

#             combined_text = transcription + "\nprompt:\n" + prompt

#             improved_transcription = self._local_llm_response(combined_text)

#             return improved_transcription
#         except Exception as e:
#             print(f"Error during improve_transcription: {e}")
#             return None

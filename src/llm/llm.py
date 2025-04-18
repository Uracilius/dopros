import os
from src.llm.exceptions.llm_exceptions import LLMError
from llama_cpp import Llama
from src.llm import config


class LLM:
    def __init__(self):
        self.llm = Llama(
            model_path=config.PATH_TO_LOCAL_LLM,
            n_ctx=config.MAX_CONTEXT_WINDOW,
            n_threads=os.cpu_count(),
            use_mlock=False,
            use_mmap=True,
            chat_format="llama-3",
        )

    def local_llm(self, system_prompt, user_prompt, max_tokens=config.MAX_TOKENS):
        return self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.4,
            top_k=40,
            top_p=0.95,
            repeat_penalty=1.1,
        )

    def improve_transcription(
        self,
        text_or_path,
        prompt_path="src/llm/prompts/improve_transcription_prompt_uni.txt",
    ):
        try:
            transcription = self._smart_text_detect(text_or_path)

            with open(prompt_path, "r", encoding="utf-8") as prompt_file:
                system_prompt = prompt_file.read().strip()

            user_prompt = transcription.strip()

            result = self.local_llm(system_prompt, user_prompt, max_tokens=2048)
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error during improve_transcription: {e}")
            return None

    def summarize(
        self, text_or_path, prompt_path="src/llm/prompts/summarize_prompt_uni.txt"
    ):
        try:
            content = self._smart_text_detect(text_or_path)

            with open(prompt_path, "r", encoding="utf-8") as prompt_file:
                system_prompt = prompt_file.read().strip()

            user_prompt = content.strip()

            result = self.local_llm(system_prompt, user_prompt, max_tokens=1024)
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error during summarize: {e}")
            raise LLMError("Local LLM error during summarize")

    def _smart_text_detect(self, text_or_path):
        if os.path.isfile(text_or_path):
            with open(text_or_path, "r", encoding="utf-8") as file:
                return file.read()
        return text_or_path

    def analyze(self, text):
        return text

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

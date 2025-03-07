import requests
import json
import os
from llm.exceptions.llm_exceptions import KazakhLLMError
class LLM:

    def _get_kazakh_llm_response(self, text, url="http://localhost:1234/v1/chat/completions"):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "model": "checkpoints_llama8b_031224_18900",
            "messages": [
                {"role": "system", "content": "Сізге транскрипция қатесін түзету тапсырылған. Тек түзетілген нұсқаны қайтарыңыз. Қосымша түсініктеме, ескертпе, не басқа мәтін жазбаңыз."},
                {"role": "user", "content": text}
            ],
            "max_tokens": -1,  # Control output length
            "stop": ["\n\n", "Қосымша"],  # Stop generation if unwanted text appears
            "temperature": 0.1,  # Reduce randomness for better consistency
            "top_p": 0.95,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.encoding='utf-8'
            response.raise_for_status()
            result = response.json()
            print(result)

            if "choices" not in result or not result["choices"]:
                raise KazakhLLMError("Invalid response format from Kazakh LLM")
            
            return result["choices"][0]["message"].get("content", text).strip()
        except requests.exceptions.RequestException as e:
            raise KazakhLLMError("Kazakh LLM unreachable")
    
    def improve_kazakh_transcription(self, text_or_path, prompt_path="llm/prompts/improve_transcription_prompt_kz.txt"):
        try:                
            transcription = self._smart_text_detect(text_or_path)
            
            with open(prompt_path, 'r', encoding='utf-8') as prompt_file:
                prompt = prompt_file.read()
            
            combined_text = transcription + "\nprompt:\n" + prompt
            
            improved_transcription = self._get_kazakh_llm_response(combined_text)
            
            return improved_transcription
        except Exception as e:
            print(f"Error during improve_kazakh_transcription: {e}")
            return None

    def summarize(self, text_or_path, prompt_path="llm/prompts/summarize_prompt_kz.txt"):
        with open(prompt_path, 'r', encoding='utf-8') as prompt_file:
            prompt = prompt_file.read()

        text = self._smart_text_detect(text_or_path)

        combined_text = text + "\nprompt:\n" + prompt

        summary = self._get_kazakh_llm_response(combined_text)
        return summary
    
    def _smart_text_detect(self, text_or_path):
        """Returns text even if input is a path by reading it. Loose coupling"""
        if os.path.isfile(text_or_path):
            with open(text_or_path, 'r', encoding='utf-8') as file:
                return file.read()
        return text_or_path

    def analyze(self, text):
        # Implement logic to analyze text
        analysis = text  # Placeholder logic
        return analysis
    

    
    
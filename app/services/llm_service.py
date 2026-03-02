from abc import ABC, abstractmethod


class LLMService(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> dict:
        """
        Should return:
        {
            "response": str,
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int
        }
        """
        pass

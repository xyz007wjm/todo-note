import httpx
from PySide6.QtCore import QObject, Signal


class DeepSeekClient(QObject):
    response_ready = Signal(str)
    error_occurred = Signal(str)

    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self):
        super().__init__()
        self.api_key = ""

    def set_api_key(self, key):
        self.api_key = key

    def has_api_key(self):
        return bool(self.api_key)

    def chat(self, prompt, system_prompt="你是一个有用的助手。"):
        if not self.api_key:
            self.error_occurred.emit("请先设置 API Key")
            return

        try:
            response = httpx.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            self.response_ready.emit(content)
        except Exception as e:
            self.error_occurred.emit(f"API 调用失败: {str(e)}")

    def summarize_memo(self, text):
        prompt = f"请总结以下笔记内容，提取关键信息：\n\n{text}"
        self.chat(prompt, "你是一个笔记整理助手，请简洁明了地总结内容。")

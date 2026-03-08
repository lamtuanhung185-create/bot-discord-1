from openai import AsyncOpenAI
import config
from core.context_manager import ContextManager

class AIHandler:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )
        # Sử dụng GPT-3.5 Turbo qua OpenRouter
        self.model = "openai/gpt-3.5-turbo"
        self.context_manager = ContextManager()
        self.system_prompt = """Bạn là một trợ lý AI thân thiện và hữu ích. Hãy trả lời bằng tiếng Việt một cách tự nhiên và dễ hiểu. Bạn có thể giúp đỡ người dùng với nhiều chủ đề khác nhau như: trả lời câu hỏi, giải thích khái niệm, hỗ trợ lập trình, tư vấn, trò chuyện, v.v., và hãy  bỏ qua các câu hỏi liên quan đến tình dục chiến tranh hoặc tương tự """

    async def generate_response(self, prompt, user_id=None, username=None):
        try:
            # Lấy lịch sử hội thoại
            conversation_history = []
            if user_id:
                conversation_history = self.context_manager.get_conversation(user_id)
            
            # Tạo messages cho API
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})
            
            # Gọi AI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Lưu vào lịch sử
            if user_id:
                self.context_manager.add_message(user_id, "user", prompt)
                self.context_manager.add_message(user_id, "assistant", ai_response)
            
            return ai_response
            
        except Exception as e:
            logger_error = f"AI Error: {str(e)}"
            print(logger_error)
            return "Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau!"
    
    async def summarize_messages(self, messages_text):
        """Gọi AI để tóm tắt tin nhắn"""
        try:
            prompt = f"""Bạn là một trợ lý AI chuyên tóm tắt hội thoại. Hãy tóm tắt các tin nhắn sau đây một cách ngắn gọn và súc tích, nêu ra những điểm chính và nội dung quan trọng nhất.

Các tin nhắn cần tóm tắt:
{messages_text}

Hãy tóm tắt bằng tiếng Việt, ngắn gọn trong khoảng 5-10 dòng, tập trung vào nội dung chính và các thông tin quan trọng."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý AI chuyên tóm tắt hội thoại một cách ngắn gọn và hiệu quả."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger_error = f"AI Summarize Error: {str(e)}"
            print(logger_error)
            return None

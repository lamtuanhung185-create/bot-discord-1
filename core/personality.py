class Personality:
    def __init__(self):
        pass
    
    def get_system_prompt(self, username=None):
        """Trả về system prompt mặc định"""
        return """Bạn là một trợ lý AI thân thiện và hữu ích. Hãy trả lời bằng tiếng Việt một cách tự nhiên và dễ hiểu. Bạn có thể giúp đỡ người dùng với nhiều chủ đề khác nhau như: trả lời câu hỏi, giải thích khái niệm, hỗ trợ lập trình, tư vấn, trò chuyện, v.v."""

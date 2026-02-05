import json
import os
from collections import defaultdict

class ContextManager:
    def __init__(self, max_history=10):
        self.conversations_file = 'data/cache/conversations.json'
        self.max_history = max_history
        self.conversations = self.load_conversations()
    
    def load_conversations(self):
        try:
            if os.path.exists(self.conversations_file):
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading conversations: {e}")
        return {}
    
    def save_conversations(self):
        try:
            os.makedirs(os.path.dirname(self.conversations_file), exist_ok=True)
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving conversations: {e}")
    
    def get_conversation(self, user_id):
        """Lấy lịch sử hội thoại của user"""
        return self.conversations.get(user_id, [])
    
    def add_message(self, user_id, role, content):
        """Thêm tin nhắn vào lịch sử"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "role": role,
            "content": content
        })
        
        # Giới hạn số lượng tin nhắn lưu trữ
        if len(self.conversations[user_id]) > self.max_history * 2:
            self.conversations[user_id] = self.conversations[user_id][-(self.max_history * 2):]
        
        self.save_conversations()
    
    def clear_conversation(self, user_id):
        """Xóa lịch sử hội thoại của user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            self.save_conversations()
            return True
        return False

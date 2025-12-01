import json
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import AsyncOpenAI
from django.conf import settings
from channels.db import database_sync_to_async
from .models import ChatMessage
from scans.models import FaceScan, UserGoal
from payments.services import verify_subscription_status

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # 1. BARRIER: Payment Check
        is_premium = await verify_subscription_status(self.user)
        
        if not is_premium:
            await self.accept()
            await self.send(text_data=json.dumps({
                'sender': 'System',
                'error': 'PAYMENT_REQUIRED',
                'message': 'Chat is a Premium feature. Please subscribe.'
            }))
            await self.close()
            return

        await self.accept()
        
        history = await self.get_chat_history()
        
        if history:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'messages': history
            }))
        else:
            greeting_text = f"Hi {self.user.name}! I'm FaceCoach. Ask me anything about your routine or scans."
            await self.save_message(self.user, 'AI', greeting_text)
            await self.send(text_data=json.dumps({
                'sender': 'AI',
                'message': greeting_text
            }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            user_message = data.get('message')
        except json.JSONDecodeError:
            user_message = text_data

        if not user_message:
            return

        await self.save_message(self.user, 'USER', user_message)

        context_str = await self.get_user_context()

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"You are FaceCoach. User Data: {context_str}. Keep answers short."},
                    {"role": "user", "content": user_message}
                ]
            )
            ai_reply = response.choices[0].message.content

            await self.save_message(self.user, 'AI', ai_reply)

            await self.send(text_data=json.dumps({
                'sender': 'AI',
                'message': ai_reply
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    @database_sync_to_async
    def save_message(self, user, sender, message):
        return ChatMessage.objects.create(user=user, sender=sender, message=message)

    @database_sync_to_async
    def get_chat_history(self):
        messages = ChatMessage.objects.filter(user=self.user).order_by('created_at')
        return [
            {
                'sender': msg.sender,
                'message': msg.message,
                'created_at': msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for msg in messages
        ]

    @database_sync_to_async
    def get_user_context(self):
        scan = FaceScan.objects.filter(user=self.user).last()
        goal = UserGoal.objects.filter(user=self.user).first()
        context = ""
        if scan:
            context += f"Jaw: {scan.jawline_angle}, Sym: {scan.symmetry_score}%. "
        if goal:
            context += f"Targets: Jaw {goal.target_jawline}. "
        return context
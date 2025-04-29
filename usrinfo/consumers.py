# yourapp/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class AvatarConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('here')
        print("🔥 WebSocket CONNECT received!!")
        user = self.scope['user']
        if user.is_authenticated:
            self.user_id = user.id
            print('userid:',self.user_id)
            self.group_name = f"user_{self.user_id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            print('accepting websocket')
            await self.accept()
        else:
            print("🔥 WebSocket CONNECT closed imm!!")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def avatar_ready(self, event):
        print('consumer...sending')
        await self.send(text_data=json.dumps({
            "message": "Avatar is ready!",
            "avatar_url": event["avatar_url"]
        }))

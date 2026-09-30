import json
from dependency.redis import redis_client
from schema.conversation_schema import ConversationState

class SessionService:
    
    PREFIX = "conversation"
    def _key(self,user_id:str):

        return f"{self.PREFIX}:{user_id}"

    async def get( self, user_id:str ) -> ConversationState | None:
        
        key = self._key(user_id)

        data = await redis_client.get(key)

        if not data:
            return None

        return ConversationState(
            **json.loads(data)
        )

    async def create(self, user_id:str):

        session = ConversationState(
            user_id=user_id
        )

        await self.save(session)

        return session



    async def save(
        self,
        session:ConversationState
    ):

        key = self._key(
            session.user_id
        )

        await redis_client.set(
            key,
            session.model_dump_json(),
            ex=1800
        )
        

    def add_message(
        self,
        session: ConversationState,
        role:str,
        content:str
    ):


        if not session:
            raise

        session.history.append(
            {
                "role":role,
                "content":content
            }
        )
        
        return session



    def update_task(
        self,
        session: ConversationState,
        intent:str,
        slots:dict
    ):

        if not session:
            raise

        existing_slots = (
            session.task.slots
        )

        merged_slots = {
            **existing_slots,
            **slots
        }

        session.mode = "task"
        session.task.intent = intent
        session.task.status = "collecting"
        session.task.slots = merged_slots

        return session



    def clear_task(
        self,
        session: ConversationState
    ):
        
        if session:

            session.task.intent = None
            session.task.status = "idle"
            session.task.slots = {}
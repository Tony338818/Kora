
from collections.abc import Callable

from redis.exceptions import WatchError

from dependency.redis import redis_client
from schema.conversation_schema import ConversationState, TaskStatus


class SessionService:
    PREFIX = "conversation"

    def __init__(self, ttl: int = 1800):
        self.ttl = ttl

    def _key(self, user_id: str) -> str:
        return f"{self.PREFIX}:{user_id}"

    async def get(
        self, user_id: str
    ) -> ConversationState | None:
        data = await redis_client.get(self._key(user_id))

        if data is None:
            return None

        return ConversationState.model_validate_json(data)

    async def create(self, user_id: str) -> ConversationState:
        state = ConversationState(user_id=user_id)

        created = await redis_client.set(
            self._key(user_id),
            state.model_dump_json(),
            ex=self.ttl,
            nx=True,
        )

        if not created:
            return await self.get(user_id)

        return state

    async def save(self, state: ConversationState):
        await redis_client.set(
            self._key(state.user_id),
            state.model_dump_json(),
            ex=self.ttl,
        )

    async def delete(self, user_id: str):
        await redis_client.delete(self._key(user_id))

    async def update(
        self,
        user_id: str,
        transition: Callable,
        retries: int = 5,
        *,
        message_id: str | None = None,
    ):
        key = self._key(user_id)
        receipt = f"conversation-message:{user_id}:{message_id}" if message_id else None

        for attempt in range(retries):
            try:
                async with redis_client.pipeline(
                    transaction=True
                ) as pipe:
                    await pipe.watch(*(key, receipt) if receipt else (key,))
                    if receipt:
                        if await pipe.exists(receipt):
                            return None, None

                    raw = await pipe.get(key)

                    if raw:
                        state = ConversationState.model_validate_json(
                            raw
                        )
                    else:
                        state = ConversationState(user_id=user_id)

                    was_executing = state.task.status == TaskStatus.EXECUTING
                    result = transition(state)
                    state.version += 1
                    # Polling a stranded execution must not keep it alive indefinitely.
                    expiration = (
                        {"keepttl": True}
                        if was_executing and state.task.status == TaskStatus.EXECUTING
                        else {"ex": self.ttl}
                    )

                    pipe.multi()
                    pipe.set(
                        key,
                        state.model_dump_json(),
                        **expiration,
                    )
                    if receipt:
                        pipe.set(receipt, "received", ex=86400)
                    await pipe.execute()

                    return state, result

            except WatchError:
                if attempt == retries - 1:
                    raise RuntimeError(
                        "Session update failed due to concurrent changes"
                    )

        raise RuntimeError("Session update failed")

import asyncio
from types import SimpleNamespace

import pytest

from ai import orchestrator
from schema.conversation_schema import ConversationState, TaskStatus
from schema.db_schema import Products, Transactions


class Classifier:
    def __init__(self, classify):
        self.classify = classify
        self.calls = []

    def predict(self, message):
        self.calls.append(message)
        return [f"__label__{self.classify(message)}"], [1.0]


class MemorySessions:
    def __init__(self):
        self.states = {}
        self.messages = set()

    async def update(self, user_id, transition, *, message_id=None):
        key = (user_id, message_id)
        if message_id and key in self.messages:
            return None, None
        state = self.states.get(user_id, ConversationState(user_id=user_id)).model_copy(deep=True)
        action = transition(state)
        self.states[user_id] = state
        if message_id:
            self.messages.add(key)
        await asyncio.sleep(0)
        return state, action


@pytest.fixture
def dialogue(monkeypatch, db_session, test_user):
    conversation = Classifier(lambda _: "INVENTORY")
    inventory = Classifier(
        lambda message: (
            "VIEW_INVENTORY" if message.startswith("show")
            else "UPDATE_PRODUCT" if message.startswith(("update", "reduce"))
            else "ADD_PRODUCT"
        )
    )

    def nlp(message):
        # Regression for an NER model labelling a corrected quantity as a price.
        entities = (
            [SimpleNamespace(label_="COST_PRICE", text="8", start_char=9)]
            if message == "quantity 8" else []
        )
        return SimpleNamespace(ents=entities)

    models = SimpleNamespace(
        conversation_classifier=conversation,
        inventory_classifier=inventory,
        inventory_bot=nlp,
    )
    request = SimpleNamespace(app=SimpleNamespace(state=models))
    sessions = MemorySessions()
    monkeypatch.setattr(orchestrator, "session_service", sessions)

    async def send(message, message_id=None):
        return await orchestrator.process_message(
            db_session, test_user.id, message, test_user.phone_number, request, message_id,
        )

    return send, models, sessions


def test_inventory_waits_for_confirmation_and_applies_only_corrected_field(dialogue, db_session):
    send, models, _ = dialogue

    async def scenario():
        assert "quantity" in (await send("add rice"))["message"]
        assert "cost price" in (await send("5"))["message"]
        assert "selling price" in (await send("2.40"))["message"]
        assert "confirm" in (await send("4.50"))["message"]
        assert "quantity = 8" in (await send("actually quantity 8"))["message"]
        assert not db_session.query(Products).count()

        replies = await asyncio.gather(send("yes", "SM123"), send("yes", "SM123"))
        assert sum(reply.get("duplicate", False) for reply in replies) == 1
        product = db_session.query(Products).one()
        assert (product.quantity, product.cost_price, product.selling_price) == (8, 2.4, 4.5)
        assert "no request" in (await send("yes", "SM124"))["message"]

    asyncio.run(scenario())
    assert models.conversation_classifier.calls == ["add rice"]
    assert models.inventory_classifier.calls == ["add rice"]


def test_cancel_and_switch_clear_collected_fields(dialogue, db_session):
    send, _, sessions = dialogue

    async def scenario():
        await send("add rice")
        assert (await send("cancel"))["message"] == "Cancelled."
        assert "no request" in (await send("yes"))["message"]
        await send("add coke")
        assert "empty" in (await send("show inventory"))["message"]
        task = next(iter(sessions.states.values())).task
        assert task.status == TaskStatus.COMPLETED
        assert not task.slots
        assert not db_session.query(Products).count()

    asyncio.run(scenario())


def test_sale_validates_then_records_and_can_be_looked_up(dialogue, db_session, test_user):
    send, _, _ = dialogue
    product = Products(name="rice", quantity=5, user_id=test_user.id)
    db_session.add(product)
    db_session.commit()

    async def scenario():
        await send("record a sale")
        await send("rice")
        await send("-2")
        await send("5")
        await send("cash")
        assert not (await send("paid"))["success"]
        assert "confirm" in (await send("2"))["message"]
        assert not db_session.query(Transactions).count()
        confirmed, duplicate = await asyncio.gather(send("yes", "SMsale"), send("yes", "SMsale"))
        assert confirmed["success"], confirmed["message"]
        assert duplicate["duplicate"]
        transaction = db_session.query(Transactions).one()
        db_session.refresh(product)
        assert (product.quantity, transaction.amount) == (3, 10)
        assert f"Transaction #{transaction.id}" in (await send(f"get transaction {transaction.id}"))["message"]

    asyncio.run(scenario())


def test_stock_delta_uses_current_stock(dialogue, db_session, test_user):
    send, _, _ = dialogue
    product = Products(name="rice", quantity=12, user_id=test_user.id)
    db_session.add(product)
    db_session.commit()

    async def scenario():
        assert "confirm" in (await send(f"reduce product {product.id} stock by 5"))["message"]
        assert (await send("yes"))["success"]
        db_session.refresh(product)
        assert product.quantity == 7

    asyncio.run(scenario())

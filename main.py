# from fastapi import FastAPI, Request, Depends, Form
# from routers import user_router, inventory_router, transactions_router
# from pydantic import BaseModel, Field
# from typing import Optional, Annotated
# from ai.orchestrator import process_message
# from dependency.session import create_session

# app = FastAPI(
#     version='0.1',
#     description='Business Operations Support System'
# )

# app.include_router(user_router.router)
# app.include_router(inventory_router.router)
# app.include_router(transactions_router.router)


# class TwilioMessage(BaseModel):
#     sms_sid: str = Field(alias="SmsSid")
#     sms_status: str = Field(alias="SmsStatus")
#     body: str = Field(alias="Body")
#     from_number: str = Field(alias="From")
#     to_number: str = Field(alias="To")
#     num_media: int = Field(alias="NumMedia", default=0)
#     profile_name: Optional[str] = Field(alias="ProfileName", default=None)

#     class Config:
#         populate_by_name = True
        
# @app.post("/webhook")
# async def webhook(data: Annotated[TwilioMessage, Depends()], ):
#     process_message()


from fastapi import FastAPI, Form

from ai.orchestrator import process_message
from services.messaging_service import send_message  # adjust path if needed

app = FastAPI(
    version='0.1',
    description='Business Operations Support System'
)



# ── WEBHOOK ───────────────────────────────────

@app.post("/webhook")
async def webhook(
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    ProfileName: str = Form(default=None)
):
    
    print("🔥 WEBHOOK HIT")
    print(f"Message: {Body}")
    print(f"From: {From}")
    user_id = From
    message = Body

    # 🔥 Call orchestrator
    result = process_message(user_id, message)

    # ── HANDLE RESPONSE ─────────────────────────

    if result["status"] == "clarification":
        send_message(result["message"], user_id)
        return {"status": "ok"}

    if result["status"] == "unknown":
        send_message(result["message"], user_id)
        return {"status": "ok"}

    if result["status"] == "ready":
        response_text = _handle_business_logic(result)
        send_message(response_text, user_id)
        return {"status": "ok"}

    return {"status": "error"}


# ── MOCK BACKEND (TEMP) ───────────────────────

def _handle_business_logic(result: dict) -> str:
    intent = result["intent"]
    data = result["data"]

    if intent == "add_product":
        return f"✅ Product '{data['name']}' added successfully with {data['quantity']} units."

    if intent == "increment_stock_quantity":
        return f"✅ Stock updated. Added {data['quantity']} units to {data['name']}."

    if intent == "record_sale":
        return "✅ Sale recorded successfully."

    return "✅ Operation completed successfully."
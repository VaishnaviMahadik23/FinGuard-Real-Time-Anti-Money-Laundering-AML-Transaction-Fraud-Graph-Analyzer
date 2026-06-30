"""Accounts API"""
from fastapi import APIRouter, HTTPException
from app.models.account import Account
from app.schemas.schemas import AccountCreate, AccountResponse

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(payload: AccountCreate):
    acc = Account(**payload.model_dump())
    await acc.insert()
    return acc


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(limit: int = 100):
    return await Account.find_all().limit(limit).to_list()


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str):
    acc = await Account.find_one({"account_id": account_id})
    if not acc:
        raise HTTPException(404, "Account not found")
    return acc


@router.post("/{account_id}/freeze")
async def freeze_account(account_id: str):
    acc = await Account.find_one({"account_id": account_id})
    if not acc:
        raise HTTPException(404, "Account not found")
    acc.is_frozen = True
    await acc.save()
    return {"status": "frozen", "account_id": account_id}

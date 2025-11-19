# app/services/auth_service.py
from app.crud.user import get_user_by_mobile, create_user_db
from app.core.security import verify_password, get_password_hash, create_access_token
from fastapi import HTTPException, status

async def register_user(mobile: str, role: str):
    user = await get_user_by_mobile(mobile)
    if user:
        raise HTTPException(status_code=400, detail="این شماره موبایل قبلاً ثبت شده است")
    
    # رمز پیش‌فرض همیشه 123456 → هش ثابت
    password_hash = get_password_hash("123456")
    await create_user_db(mobile=mobile, password_hash=password_hash, role=role)
    return {"message": f"کاربر {mobile} با موفقیت ثبت شد | نقش: {role} | کیف پول: ۱۰٬۰۰۰٬۰۰۰ تومان"}

async def login_user(mobile: str, password: str):
    user = await get_user_by_mobile(mobile)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="موبایل یا رمز عبور اشتباه")
    
    access_token = create_access_token({"sub": mobile})
    return {"access_token": access_token, "token_type": "bearer"}
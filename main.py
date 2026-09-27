from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings, load_app_config
from app.connectors.servicenow import ServiceNowConnector
from app.database import SessionLocal, get_session, initialise_database
from app.dummy_servicenow import router as dummy_router
from app.models import User
from app.repository import TicketRepository, audit
from app.schemas import TokenResponse
from app.security import Identity, authenticate, create_token, hasher, require_roles

@asynccontextmanager
async def lifespan(app:FastAPI):
    await initialise_database()
    async with SessionLocal() as s:
        for username,password,role in [("admin","Admin123!","admin"),("engineer","Engineer123!","engineer"),("viewer","Viewer123!","viewer")]:
            if not (await s.execute(select(User).where(User.username==username))).scalar_one_or_none():
                s.add(User(username=username,password_hash=hasher.hash(password),role=role))
        await s.commit()
    yield

app=FastAPI(title="ServiceNow Connector Learning Project",lifespan=lifespan)
app.include_router(dummy_router)
@app.get("/health")
async def health():
    return {"status":"ok"}
@app.post("/auth/token",response_model=TokenResponse)
async def token(form:OAuth2PasswordRequestForm=Depends(),session:AsyncSession=Depends(get_session)):
    user=await authenticate(session,form.username,form.password)
    if not user: raise HTTPException(401,"Invalid credentials",headers={"WWW-Authenticate":"Bearer"})
    return TokenResponse(access_token=create_token(user))
@app.post("/ingestion/servicenow")
async def ingest(identity:Identity=Depends(require_roles("engineer","admin")),session:AsyncSession=Depends(get_session)):
    cfg=load_app_config(); s=get_settings(); http_cfg=cfg["http"]; sn_cfg=cfg["servicenow"]
    connector=ServiceNowConnector(s.servicenow_base_url,s.servicenow_token,http_cfg["timeout_seconds"],http_cfg["maximum_attempts"])
    try:
        page=await connector.fetch_approved(sn_cfg["assignment_group"],sn_cfg["batch_size"])
        count=await TicketRepository(session).upsert_many(page.items)
        await audit(session,identity.username,"servicenow_ingestion","success",f"persisted={count}")
        await session.commit()
        return {"fetched":len(page.items),"persisted":count,"requested_by":identity.username}
    except Exception as exc:
        await session.rollback(); raise HTTPException(502,"Ingestion failed") from exc
    finally: await connector.close()
@app.get("/tickets")
async def tickets(identity:Identity=Depends(require_roles("viewer","engineer","admin")),session:AsyncSession=Depends(get_session)):
    rows=await TicketRepository(session).list_all()
    return [{"number":r.number,"state":r.state,"assignment_group":r.assignment_group,"short_description":r.short_description} for r in rows]

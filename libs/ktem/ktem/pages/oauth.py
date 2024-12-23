import os

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")


config_data = {
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
    "GOOGLE_REDIRECT_URI": GOOGLE_REDIRECT_URI,
}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/m")
    return RedirectResponse(url="/login")


@app.get("/login/google")
async def login(request: Request):
    redirect_uri = request.url_for("auth/google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@app.get("/auth/google")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f"<h1>{error.error}</h1>")
    user_info = token.get("userinfo")
    if user_info:
        request.session["user"] = user_info
    return RedirectResponse(url="/")

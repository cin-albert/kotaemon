import hashlib

import gradio as gr
from ktem.app import BasePage
from ktem.db.models import User, engine
from sqlmodel import Session, select


class SignupPage(BasePage):

    public_events = ["onSignUpGoogle", "onSignUpGitHub", "onSignUp"]

    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        gr.Markdown(f"# Welcome to {self._app.app_name}!")

        self.usn = gr.Textbox(label="Username", visible=False)
        self.pwd = gr.Textbox(label="Password", type="password", visible=False)
        self.pwd_confirm = gr.Textbox(
            label="Confirm Password", type="password", visible=False
        )
        self.btn_signup = gr.Button("Sign Up", visible=False)

        gr.Markdown("### OR")
        self.btn_google_signup = gr.Button("Sign Up with Google")

    def on_register_events(self):
        onSignUp = gr.on(
            triggers=[self.btn_signup.click],
            fn=self.signup,
            inputs=[self.usn, self.pwd, self.pwd_confirm],
            outputs=[self._app.user_id, self.usn, self.pwd, self.pwd_confirm],
            show_progress="hidden",
        ).then(
            self.toggle_signup_visibility,
            inputs=[self._app.user_id],
            outputs=[self.usn, self.pwd, self.pwd_confirm, self.btn_signup],
        )
        for event in self._app.get_event("onSignUp"):
            onSignUp = onSignUp.success(**event)

        onSignUpGoogle = gr.on(
            triggers=[self.btn_google_signup.click],
            fn=self.signup,
            outputs=[self._app.user_id, self.usn, self.pwd, self.pwd_confirm],
            show_progress="hidden",
        )
        for event in self._app.get_event("onSignUpGoogle"):
            onSignUpGoogle = onSignUpGoogle.success(**event)

    def _on_app_created(self):
        onSignUp = self._app.app.load(
            self.signup,
            inputs=[self.usn, self.pwd, self.pwd_confirm],
            outputs=[self._app.user_id, self.usn, self.pwd, self.pwd_confirm],
            show_progress="hidden",
        ).then(
            self.toggle_signup_visibility,
            inputs=[self._app.user_id],
            outputs=[self.usn, self.pwd, self.pwd_confirm, self.btn_signup],
        )
        for event in self._app.get_event("onSignUp"):
            onSignUp = onSignUp.success(**event)

    def toggle_signup_visibility(self, user_id):
        return (
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
            gr.update(visible=user_id is None),
        )

    def on_subscribe_public_events(self):
        self._app.subscribe_event(
            name="onSignOut",
            definition={
                "fn": self.toggle_signup_visibility,
                "inputs": [self._app.user_id],
                "outputs": [self.usn, self.pwd, self.pwd_confirm, self.btn_signup],
                "show_progress": "hidden",
            },
        )

    def signup(self, username, password, password_confirm):
        if password != password_confirm:
            return False
        is_created, user_id = self.create_user(username, password)
        if not is_created:
            return None, "", "", ""
        return user_id, username, password, password_confirm

    def create_user(self, usn, pwd) -> tuple[bool, int | None]:
        if not usn or not pwd:
            return False, None

        with Session(engine) as session:
            statement = select(User).where(User.username_lower == usn.lower())
            result = session.exec(statement).all()
            if result:
                print(f'User "{usn}" already exists')
                gr.Info("User already exists")
                return False, None
            else:
                hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
                user = User(
                    username=usn,
                    username_lower=usn.lower(),
                    password=hashed_password,
                    admin=False,
                )
                session.add(user)
                session.commit()

                return True, user.id

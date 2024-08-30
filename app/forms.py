from wtforms import StringField, SubmitField, PasswordField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class CreateUserForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=3, max=30)])
    carbon_login = StringField(
        "Carbon Логин",
        render_kw={'placeholder': 'не обязательно'},
        validators=[Length(min=3, max=30)]
    )
    carbon_passw = PasswordField(
        "Carbon Пароль",
        render_kw={'placeholder': 'не обязательно'},
        validators=[Length(min=3, max=30)]
    )
    privilege = SelectField("Уровень прав", choices=[('admin', 'Администратор'), ('user', 'Пользователь')])
    submit = SubmitField('Создать')


class ChangeUserForm(FlaskForm):
    username = StringField("Логин", validators=[Length(max=30)])
    password = PasswordField("Пароль", validators=[Length(max=30)])
    carbon_login = StringField("Carbon Логин", validators=[Length(max=30)])
    carbon_passw = PasswordField("Carbon Пароль", validators=[Length(max=30)])
    privilege = SelectField("Уровень прав", choices=[
        ('none', ''),
        ('admin', 'Администратор'),
        ('user', 'Пользователь'),
    ])
    submit = SubmitField('Применить')


class CreateHostForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired(), Length(min=5, max=100)])
    ip = StringField("IP адрес", validators=[DataRequired(), Length(max=50)])
    folder = SelectField("Папка")
    submit = SubmitField('Создать')


class ChangeHostForm(CreateHostForm):
    submit = SubmitField('Изменить')
    pause = SelectField('Пауза', choices=[('pause', 'Вкл.'), ('offline', 'Выкл.')])


class CreateFolderForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired(), Length(min=5, max=50)])
    submit = SubmitField('Создать')


class ChangeFolderForm(CreateFolderForm):
    submit = SubmitField('Изменить')


class ChangeIcmpParams(FlaskForm):
    ping_interval = IntegerField(validators=[DataRequired()])
    icmp_count = IntegerField(validators=[DataRequired()])
    icmp_interval = IntegerField(validators=[DataRequired()])
    ping_workers = IntegerField(validators=[DataRequired()])
    icmp_timeout = IntegerField(validators=[DataRequired()])
    submit = SubmitField('Применить')
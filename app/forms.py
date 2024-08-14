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


class ChangeGponParams(FlaskForm):
    name = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Название',
                                                               'autocomplete': 'off'})
    tag = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 20, 'placeholder': 'Тег',
                                                              'autocomplete': 'off'})
    ip = StringField(validators=[DataRequired()], render_kw={'min': 4, 'max': 20, 'placeholder': 'IP',
                                                             'autocomplete': 'off'})
    port = IntegerField(validators=[DataRequired()], render_kw={'placeholder': 'Порт',
                                                                'autocomplete': 'off'})
    login = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Логин',
                                                                'autocomplete': 'off'})
    passw = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Пароль',
                                                                'autocomplete': 'off'})
    submit = SubmitField('Применить')


class CreateGponProfile(FlaskForm):
    name = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Название',
                                                               'autocomplete': 'off'})
    vlan = IntegerField(validators=[DataRequired()], render_kw={'min': 1, 'max': 4096, 'placeholder': 'VLAN id',
                                                                'autocomplete': 'off'})
    gemport = IntegerField(validators=[DataRequired()], render_kw={'placeholder': 'VLAN id',
                                                                   'autocomplete': 'off'})
    srv_profile = IntegerField(validators=[DataRequired()], render_kw={'placeholder': 'Service-профиль',
                                                                       'autocomplete': 'off'})
    line_profile = IntegerField(validators=[DataRequired()], render_kw={'placeholder': 'Line-профиль',
                                                                        'autocomplete': 'off'})
    submit = SubmitField('Создать')


class ChangeCarbonApi(FlaskForm):
    name = StringField(label='Название', validators=[DataRequired()], render_kw={'min': 3, 'max': 50})
    ip = StringField(label='IP', validators=[DataRequired()], render_kw={'min': 4, 'max': 20})
    port = IntegerField(label='Порт', validators=[DataRequired()])
    submit = SubmitField('Применить')


class CreateNasApi(FlaskForm):
    name = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Название',
                                                               'autocomplete': 'off'})
    ip = StringField(validators=[DataRequired()], render_kw={'min': 4, 'max': 20, 'placeholder': 'IP',
                                                             'autocomplete': 'off'})
    port = IntegerField(validators=[DataRequired()], render_kw={'placeholder': 'Порт',
                                                                'autocomplete': 'off'})
    login = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Логин',
                                                                'autocomplete': 'off'})
    passw = StringField(validators=[DataRequired()], render_kw={'min': 3, 'max': 50, 'placeholder': 'Пароль',
                                                                'autocomplete': 'off'})
    submit = SubmitField('Создать')


class ChangeForwardGateway(FlaskForm):
    external_ip = StringField(
        label='IP',
        validators=[DataRequired()], render_kw={'min': 4, 'max': 20, 'placeholder': 'IP', 'autocomplete': 'off'}
    )
    external_port = IntegerField(
        label='Port',
        validators=[DataRequired()], render_kw={'placeholder': 'Порт', 'autocomplete': 'off'}
    )
    submit = SubmitField('Применить')



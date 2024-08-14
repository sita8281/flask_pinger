from app import app, db
from app.models import User, Host, HostFolder

# runner
# html 0.2


@app.shell_context_processor
def make_shell_context():
    return {'app': app, 'db': db, 'User': User, 'Host': Host, 'HostFolder': HostFolder}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, use_reloader=False)




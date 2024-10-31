# Contains the application factory
# Tells python the virtualpet directory is a package

import os
from flask import Flask

# application factory function
def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'virtualpet.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # simple starter page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'


    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import pet
    app.register_blueprint(pet.bp)
    app.add_url_rule('/', endpoint='index')

    return app



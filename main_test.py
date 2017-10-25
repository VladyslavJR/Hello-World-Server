import webtest

import main


def test_get():
    app = webtest.TestApp(main.app)

    response = app.get('/')

    assert response.status == 200
    assert response.body == 'Hello, World!'

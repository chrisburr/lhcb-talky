#!/usr/bin/env python
import os
import talky
import unittest
import tempfile
import shutil


class TalkyTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a dummy DB
        self.db_fd, talky.app.config['DATABASE'] = tempfile.mkstemp()
        talky.app.config['TESTING'] = False
        # Disable CSRF tokens for unit tests
        talky.app.config['WTF_CSRF_ENABLED'] = False
        # Set up a dummy location for uploaded files
        talky.app.config['file_path'] = tempfile.mkdtemp()
        talky.default_config.file_path = talky.app.config['file_path']
        #
        talky.app.config['DEBUG'] = True

        self.client = talky.app.test_client()
        with talky.app.app_context():
            # talky.db.create_all()
            print('Creating database')
            from talky import create_database
            create_database.build_sample_db(fast=True)
            print('Database created')

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(talky.app.config['DATABASE'])
        shutil.rmtree(talky.app.config['file_path'])

    # Test authentication
    def login(self, username, password):
        return self.client.post('/secure/login/', data=dict(
            email=username,
            password=password,
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/secure/logout', follow_redirects=True)

    def test_login_logout(self):
        # Valid login for admin
        rv = self.login('admin', 'admin')
        assert b'Admin mode' in rv.data
        assert b'User mode' in rv.data
        rv = self.logout()
        assert b'login_user_form' in rv.data
        # Valid login for user
        rv = self.login('userlhcb', 'user')
        assert b'LHCb - userlhcb' in rv.data
        assert b'Admin mode' not in rv.data
        rv = self.logout()
        assert b'login_user_form' in rv.data
        # Invalid logins attempts
        rv = self.login('', '')
        assert b'Email not provided' in rv.data
        rv = self.login('invalid_user', '')
        assert b'Password not provided' in rv.data
        rv = self.login('invalid_user', 'wrong_password')
        assert b'Invalid username/password combination' in rv.data
        rv = self.login('admin', 'wrong_password')
        assert b'Invalid username/password combination' in rv.data


if __name__ == '__main__':
    unittest.main()

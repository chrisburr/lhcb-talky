#!/usr/bin/env python
import unittest
from io import BytesIO

import talky


class TalkyBaseTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a dummy database
        # self.db_fd, talky.app.config['DATABASE'] = tempfile.mkstemp()
        # talky.app.config['TESTING'] = False
        # Disable CSRF tokens for unit tests
        talky.app.config['WTF_CSRF_ENABLED'] = False
        # Set up a dummy location for uploaded files
        # talky.app.config['file_path'] = tempfile.mkdtemp()
        # talky.default_config.file_path = talky.app.config['file_path']
        # Prepare the test client
        self.client = talky.app.test_client()
        # Fill the dummy database
        # with talky.app.app_context():
        #     print('Creating database')
        #     from talky import create_database
        #     create_database.build_sample_db(fast=True)
        #     print('Database created')

    def tearDown(self):
        pass
        # os.close(self.db_fd)
        # os.unlink(talky.app.config['DATABASE'])
        # shutil.rmtree(talky.app.config['file_path'])

    def login(self, username, password):
        return self.client.post('/secure/login/', data=dict(
            email=username,
            password=password,
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/secure/logout', follow_redirects=True)

    def get_talk(self, *, experiment=None):
        """Get a talk matching the criteria passed as arguments."""
        with talky.app.app_context():
            for talk in talky.schema.Talk.query.all():
                if experiment is not None and talk.experiment.name != experiment:
                    continue
                return talk
        raise ValueError('Invalid parameters passed', experiment)


class TalkyAuthTestCase(TalkyBaseTestCase):
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


class TalkyTalkViewTestCase(TalkyBaseTestCase):
    def test_check_view_key(self):
        talk = self.get_talk()

        rv = self.client.get(f'/view/{talk.id}/{talk.view_key}/')
        assert rv.status == '200 OK'
        assert talk.title.encode('utf-8') in rv.data
        assert talk.upload_key.encode('utf-8') not in rv.data

        rv = self.client.get(f'/view/{talk.id}/bad_view_key/')
        assert rv.status == '404 NOT FOUND'

        rv = self.client.get(f'/view/{talk.id}/{talk.upload_key}/')
        assert rv.status == '404 NOT FOUND'

    def test_view_as_admin(self):
        talk = self.get_talk()
        self.login('admin', 'admin')
        rv = self.client.get(f'/view/{talk.id}/{talk.view_key}/')
        self.logout()
        assert rv.status == '200 OK'
        assert talk.title.encode('utf-8') in rv.data
        assert b'Upload submission' in rv.data
        assert talk.upload_key.encode('utf-8') in rv.data

    def test_view_as_user(self):
        talk = self.get_talk(experiment='LHCb')

        self.login('userlhcb', 'user')
        rv = self.client.get(f'/view/{talk.id}/{talk.view_key}/')
        self.logout()
        assert rv.status == '200 OK'
        assert talk.title.encode('utf-8') in rv.data
        assert b'Upload submission' in rv.data
        assert talk.upload_key.encode('utf-8') in rv.data

        self.login('userbelle', 'user')
        rv = self.client.get(f'/view/{talk.id}/{talk.view_key}/')
        self.logout()
        assert rv.status == '200 OK'
        assert talk.title.encode('utf-8') in rv.data
        assert b'Upload submission' not in rv.data
        assert talk.upload_key.encode('utf-8') not in rv.data


class TalkySubmissionTestCase(TalkyBaseTestCase):
    def test_check_upload_key(self):
        talk = self.get_talk()

        rv = self.client.get(f'/upload/{talk.id}/{talk.upload_key}/')
        assert rv.status == '200 OK'
        assert talk.title.encode('utf-8') in rv.data

        rv = self.client.get(f'/upload/{talk.id}/bad_upload_key/')
        assert rv.status == '404 NOT FOUND'

        rv = self.client.get(f'/upload/{talk.id}/{talk.view_key}/')
        assert rv.status == '404 NOT FOUND'

    def test_upload(self):
        talk = self.get_talk()

        with talky.app.app_context():
            before = {
                s.id: (s.filename, s.version)
                for s in talky.schema.Talk.query.get(talk.id).submissions.all()
            }
        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(file=(BytesIO(b' '*1024*1024*10), 'large_file.pdf')),
            follow_redirects=True
        )
        assert rv.status == '200 OK'
        with talky.app.app_context():
            after = {
                s.id: (s.filename, s.version)
                for s in talky.schema.Talk.query.get(talk.id).submissions.all()
            }
        # Validate the new submission and uploaded file
        new_submissions = set(after.items()) - set(before.items())
        assert len(new_submissions) == 1
        submission_id, (fn, version) = new_submissions.pop()
        fn = f'{talky.default_config.file_path}/{talk.id}/{version}/{fn}'
        with open(fn, 'rt') as f:
            file_contents = f.read()
        assert len(file_contents) == 1024*1024*10
        assert set(file_contents) == set([' '])

    def test_upload_invalid_request(self):
        talk = self.get_talk()

        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(),
            follow_redirects=True
        )
        assert rv.status == '400 BAD REQUEST'

        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(file=(BytesIO(b'Example contents'), '')),
            follow_redirects=True
        )
        assert rv.status == '200 OK'
        assert b'No file specified' in rv.data, rv.data

    def test_upload_bad_extension(self):
        talk = self.get_talk()

        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(file=(BytesIO(b'Example contents'), 'bad_file')),
            follow_redirects=True
        )
        assert rv.status == '200 OK'
        assert b'Invalid filename or extension' in rv.data

        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(file=(BytesIO(b'Example contents'), 'bad_file.zip')),
            follow_redirects=True
        )
        assert rv.status == '200 OK'
        assert b'Invalid filename or extension' in rv.data

    def test_upload_large_file(self):
        talk = self.get_talk()

        rv = self.client.post(
            f'/upload/{talk.id}/{talk.upload_key}/',
            data=dict(file=(BytesIO(b' '*1024*1024*50), 'large_file.pdf')),
            follow_redirects=True
        )
        assert rv.status == '413 REQUEST ENTITY TOO LARGE'


class TalkyCommentsTestCase(TalkyBaseTestCase):
    pass


if __name__ == '__main__':
    unittest.main()

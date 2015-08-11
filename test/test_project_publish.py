# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
from mock import patch

from default import db
from factories import ProjectFactory, AuditlogFactory, UserFactory
from helper import web
from pybossa.repositories import UserRepository
from pybossa.repositories import ProjectRepository
from pybossa.view.projects import render_template

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestProjectPublicationView(web.Helper):

    @patch('pybossa.view.projects.ensure_authorized_to')
    def test_it_checks_permissions_over_project(self, fake_auth):
        owner = UserFactory.create(email_addr='a@a.com')
        owner.set_password('1234')
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, published=False)
        self.signin(email='a@a.com', password='1234')

        post_resp = self.app.get('/project/%s/publish' % project.short_name)
        get_resp = self.app.post('/project/%s/publish' % project.short_name)

        call_args = fake_auth.call_args_list

        assert fake_auth.call_count == 2, fake_auth.call_count
        assert call_args[0][0][0] == 'update', call_args[0]
        assert call_args[0][0][1].id == project.id, call_args[0]
        assert call_args[1][0][0] == 'update', call_args[1]
        assert call_args[1][0][1].id == project.id, call_args[1]

    @patch('pybossa.view.projects.render_template', wraps=render_template)
    def test_it_renders_template_when_get(self, fake_render):
        owner = UserFactory.create(email_addr='a@a.com')
        owner.set_password('1234')
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, published=False)
        self.signin(email='a@a.com', password='1234')

        resp = self.app.get('/project/%s/publish' % project.short_name)

        call_args = fake_render.call_args_list
        assert call_args[0][0][0] == 'projects/publish.html', call_args[0]
        assert call_args[0][1]['project'].id == project.id, call_args[0]

    def test_it_changes_project_to_published_after_post(self):
        owner = UserFactory.create(email_addr='a@a.com')
        owner.set_password('1234')
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, published=False)
        self.signin(email='a@a.com', password='1234')

        resp = self.app.post('/project/%s/publish' % project.short_name,
                             follow_redirects=True)

        project = project_repo.get(project.id)
        assert resp.status_code == 200, resp.status_code
        assert project.published == True, project

    @patch('pybossa.view.projects.auditlogger')
    def test_it_logs_the_event_in_auditlog(self, fake_logger):
        owner = UserFactory.create(email_addr='a@a.com')
        owner.set_password('1234')
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, published=False)
        self.signin(email='a@a.com', password='1234')

        resp = self.app.post('/project/%s/publish' % project.short_name,
                             follow_redirects=True)

        fake_logger.add_log_entry.assert_called()

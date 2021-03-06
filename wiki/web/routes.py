"""
    Routes
    ~~~~~~
"""
import os

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import send_file
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect

from os import path
from os import getcwd

import pathlib
import sys

from re import compile

from werkzeug import secure_filename

bp = Blueprint('wiki', __name__)
uploadRegex = compile('^([^/\\\]+\\\)+$')

@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    uploads = current_wiki.indexUploads()
    return render_template('index.html', pages=pages, uploads=uploads)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/upload/', methods=['GET', 'POST'])
@protect
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # check that path is actually valid
        if request.form['path'] != '' and not request.form['path'] is None and not uploadRegex.match(request.form['path']):
            flash('Invalid path')
            return redirect(request.url)
        file = request.files['file']

        # make sure it actually has a file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            if sys.platform == 'darwin':
                os_path = str.replace(request.form['path'],"\\", "/")
            else:
                os_path = request.form['path']
            pathlib.Path(path.join(getcwd(), 'upload', os_path)).mkdir(parents=True, exist_ok=True)
            filename = secure_filename(file.filename)
            print(path.join(getcwd(), os_path, filename))
            file.save(path.join(getcwd(), 'upload', os_path, filename))
            return redirect(str.replace(request.form['path'],"\\", "/") + filename)
    uploads = current_wiki.indexUploads()
    url = request.url
    return render_template('upload.html', uploads=uploads, url=url)

@bp.route('/upload/<path:url>')
@protect
def displayUpload(url):
    if path.exists(path.join(getcwd(), 'upload' , url)):
        return send_file(path.join(getcwd(), 'upload' , url))
    return render_template('404upload.html')

@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    # check if we have an upload file or a page
    if url[0:6] == 'upload':
        # delete uploaded file
        current_wiki.deleteUpload(url)
        return redirect(url_for('wiki.upload'))
    else:
        # delete page
        page = current_wiki.get_or_404(url)
        current_wiki.delete(url)
        flash('Page "%s" was deleted.' % page.title, 'success')
        return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


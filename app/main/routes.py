from app import db
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from flask_login import current_user, login_required
from app.models import User, Post
from datetime import datetime
from app.main import bp


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    pagination = current_user.get_followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('main.index', page=pagination.next_num) if pagination.has_next else None
    prev_url = url_for('main.index', page=pagination.prev_num) if pagination.has_prev else None
    return render_template(
        'index.html', title='Home Page', form=form, posts=pagination.items,
        next_url=next_url, prev_url=prev_url
    )


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('main.explore', page=pagination.next_num) if pagination.has_next else None
    prev_url = url_for('main.explore', page=pagination.prev_num) if pagination.has_prev else None
    return render_template(
        'index.html', title='Explore', posts=pagination.items,
        next_url=next_url, prev_url=prev_url
    )


@bp.route('/user/<username>')
@login_required
def user(username):
    # Unlike other forms such as the login and edit profile forms, these two forms
    # do not have their own pages, the forms will be rendered by the user() route
    # and will appear in the user's profile page. The only reason why the validate_on_submit()
    # call can fail is if the CSRF token is missing or invalid, so in that case
    # I just redirect the application back to the home page.
    form = EmptyForm()

    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('main.user', username=user.username, page=pagination.next_num) \
        if pagination.has_next else None
    prev_url = url_for('main.user', username=user.username, page=pagination.prev_num) \
        if pagination.has_prev else None

    return render_template(
        'user.html', user=user, posts=pagination.items, form=form,
        prev_url=prev_url, next_url=next_url
    )


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()

        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You can not follow yourself!')
            return redirect(url_for('user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    return redirect(url_for('index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))

    return redirect(url_for('index'))


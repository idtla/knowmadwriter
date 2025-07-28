import pytest
from telegram_bot.models.user import User
from telegram_bot.models.site import Site
from telegram_bot.models.content import Content


@pytest.mark.asyncio
async def test_user_crud():
    user = await User.create({'telegram_id': 'u1', 'name': 'Test', 'email': 't@e.com', 'status': 'active'})
    assert user.id
    fetched = User.get_by_telegram_id('u1')
    assert fetched.email == 't@e.com'
    fetched.name = 'New'
    assert fetched.save()
    assert User.get_by_email('t@e.com').name == 'New'


@pytest.mark.asyncio
async def test_site_and_content():
    user = await User.create({'telegram_id': 'u2', 'name': 'Test2', 'email': 't2@e.com', 'status': 'active'})
    site = await Site.create({'user_id': user.id, 'name': 'MySite', 'domain': 'example.com'})
    assert site.id
    content = await Content.create({'site_id': site.id, 'title': 'Title', 'slug': 'slug', 'status': 'draft'})
    assert content.id
    fetched = Content.get_by_id(content.id)
    assert fetched.title == 'Title'
    fetched.title = 'Updated'
    assert fetched.save()
    assert Content.get_by_site_id(site.id)[0].title == 'Updated'
    assert fetched.publish()

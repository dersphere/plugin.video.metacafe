#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from xbmcswift2 import Plugin, xbmcgui
from resources.lib import scraper

STRINGS = {
    'next_videos': 30001,
    'network_error': 30150,
    'not_implemented': 30151,
}

plugin = Plugin()


@plugin.route('/')
def show_categories():
    items = [{
        'label': category['title'],
        'thumbnail': category['thumb'],
        'path': plugin.url_for(
            endpoint='show_videos',
            path=category['path'],
        )
    } for category in scraper.get_categories()]
    return plugin.finish(items)


@plugin.route('/videos/<path>/')
def show_videos(path):
    videos, next_link = scraper.get_videos(path)
    items = [{
        'label': video['title'],
        'thumbnail': video['thumb'],
        'is_playable': True,
        'info': {
            'count': i,
        },
        'path': plugin.url_for(
            endpoint='play_video',
            video_id=video['id']
        ),
    } for i, video in enumerate(videos)]
    if videos and next_link:
        items.append({
            'label': _('next_videos'),
            'info': {'count': i + 1},
            'path': plugin.url_for(
                endpoint='show_videos',
                path=next_link,
                update='true'
            )
        })
    finish_kwargs = {
        #'sort_methods': ('PLAYLIST_ORDER', 'TITLE'),
        'update_listing': 'update' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>')
def play_video(video_id):
    playable_urls = scraper.get_video_urls(video_id)
    quality = plugin.get_setting('quality', choices=('SD', 'HD'))
    playable_url = (
        playable_urls.get(quality)
        or playable_urls['SD']
        or playable_urls['flv']
    )
    log('Using URL: %s' % playable_url)
    return plugin.set_resolved_url(playable_url)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        plugin.notify(msg=_('network_error'))
    except NotImplementedError:
        plugin.notify(msg=_('not_implemented'))

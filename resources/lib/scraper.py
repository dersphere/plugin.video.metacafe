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

import json
import re
import urllib2
from urllib import unquote, urlencode
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://www.metacafe.com'
API_URL = MAIN_URL + '/api/item/%s/'
USER_AGENT = 'XBMC Add-on Metacafe'


class NetworkError(Exception):
    pass


def get_categories():
    url = MAIN_URL
    categories = []
    ul = __get_tree(url).find('ul', {'class': 'Categories'})
    for li in ul.findAll('li'):
        if not li.a:
            continue
        if 'music' in li.a['href']:
            continue
        if 'games' in li.a['href']:
            continue
        categories.append({
            'path': li.a['href'],
            'title': li.a['title'],
            'thumb': li.find('img')['src'],
        })
    return categories


def get_videos(path):

    def video_id(path):
        return path.split('/')[-3]

    url = MAIN_URL + path
    tree = __get_tree(url)
    videos = []
    ul = tree.find('ul', {'class': re.compile('ItemCatalog Group CatID2')})
    for li in ul.findAll('li'):
        div = li.find('div', {'class': 'ItemThumb'})
        a = li.find('a')
        videos.append({
            'thumb': div.img['src'],
            'title': div.img.get('title') or a.get('title') or '',
            'id': video_id(a['href'])
        })
    next_path = tree.find('a', {'class': 'LoadMore'})['href']
    if next_path:
        next_path = next_path.replace(MAIN_URL, '')
    return videos, next_path


def get_video_urls(video_id):

    def get(node):
        if node:
            vid_url = node.get('mediaURL', '')
            params = {node['access'][0]['key']: node['access'][0]['value']}
            return '%s?%s' % (vid_url, urlencode(params))

    re_json = re.compile('mediaData=([^&]+)')
    tree = __get_tree(API_URL % video_id)
    swf_url = tree.find('media:content')['url']
    if not swf_url:
        raise NotImplementedError
    resp = urllib2.urlopen(swf_url)
    match = re.search(re_json, resp.url)
    if not match:
        raise NotImplementedError
    json_data = json.loads(unquote(match.group(0)).split('=')[1])
    video_urls = {
        'HD': get(json_data.get('highDefinitionMP4', {})),
        'SD': get(json_data.get('MP4', {})),
        'FLV': get(json_data.get('flv', {}))
    }
    return video_urls


def __get_tree(url):
    log('__get_tree opening url: %s' % url)
    headers = {'User-Agent': USER_AGENT}
    req = urllib2.Request(url, None, headers)
    try:
        html = urllib2.urlopen(req).read()
    except urllib2.HTTPError, error:
        raise NetworkError('HTTPError: %s' % error)
    log('__get_tree got %d bytes' % len(html))
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def log(msg):
    print(u'%s scraper: %s' % (USER_AGENT, msg))
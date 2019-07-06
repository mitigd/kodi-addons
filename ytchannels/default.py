import sys, xbmcgui, xbmcplugin, xbmcaddon
import json
import urllib
from urlparse import parse_qsl
import re
import os
import requests
import xbmcvfs
import cookielib
import codecs
from bs4 import BeautifulSoup, SoupStrainer
from collections import OrderedDict

_handle     = int(sys.argv[1])
addon       = xbmcaddon.Addon()
addon_url   = sys.argv[0]
addondir    = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
favs_file   = os.path.join(addondir, 'favs.json')
cookie      = os.path.join(addondir, 'cookies.lwp')

def r_json(file):

    try:
        with open(addondir + file, 'r') as infile:
            data = json.load(infile, object_pairs_hook=OrderedDict)
        return data
    except:
        xbmcvfs.mkdirs(addondir)
        data = open(addondir + 'favs.json', 'w')
        data.write('{}')
        data.close()
    
def w_json(file, data):

    with codecs.open(addondir + file, 'w', encoding='utf-8') as outfile:
        str_ = json.dumps(data,
                      indent=4, sort_keys=True,
                      separators=(',', ': '), ensure_ascii=True)

        str_ = re.sub('{},', '', str(str_))
        str_ = re.sub('{}', '', str(str_))
        str_ = re.sub(r'},\n.*\n.*]\n.*}', '}]}', str(str_))
        str_ = re.sub(r'},\n.*\n.*],', '}],', str(str_))

        outfile.write(str_)


def addItem(title, params, commands, isfolder):

    url = '%s?%s' %(addon_url, urllib.urlencode(params))
    url = ''.join(url).encode('utf-8').strip()

    listItem = xbmcgui.ListItem(label=title)
    listItem.addContextMenuItems( commands )
    xbmcplugin.addDirectoryItem(_handle, url, listItem, isfolder)


def reqPage(url):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Host': 'www.youtube.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    jar = cookielib.LWPCookieJar(cookie)
    try:
        jar.load()
    except:
        pass
    s = requests.Session()
    s.cookies = jar
    get = s.get(url, headers=headers)
    res = get.content
    jar.save(ignore_discard=True)
    return res


def main():

    data = r_json('favs.json')

    try:

        for key in data:

            commands = []
            commands.append(( 'Add Category', 'XBMC.RunPlugin(' + str(addon_url) + '?action=addcat)', ))
            commands.append(('Rename Category', 'XBMC.RunPlugin(' + str(addon_url) + '?action=rencat' + '&cat=' + str(key) + ')', ))
            commands.append(( 'Delete Category', 'XBMC.RunPlugin(' + str(addon_url) + '?action=delcat' + '&cat=' + str(key) + ')', ))
            params = {"action": "channels", "folder": key}
            addItem(key, params, commands, isfolder=True)

    except:
        pass

    xbmcplugin.addDirectoryItem(_handle, '{0}?action=addcat'.format(addon_url), xbmcgui.ListItem(label='Add Category'), isFolder=False)
    xbmcplugin.endOfDirectory(_handle)


def input(str):
    kb = xbmc.Keyboard('default', 'heading', True)
    kb.setDefault('')
    kb.setHeading(str)
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        text = kb.getText()
    return text


def list_channels(folder):

    data = r_json('favs.json')

    for each in data[folder]:

        for i, x in each.items():

            channel = x.get('channel')
            commands = []
            commands.append(( 'Add Channel', 'XBMC.RunPlugin(' + str(addon_url) + '?action=addchan' + '&folder=' + folder + ')', ))
            commands.append(( 'Delete Channel', 'XBMC.RunPlugin(' + str(addon_url) + '?action=delchan' + '&folder=' + folder + '&title=' + i + ')', ))
            thumb = x.get('thumb', '')
            title = i.decode('unicode_escape')
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)
            list_item.addContextMenuItems( commands )

            if folder == 'Live':
                url = "plugin://plugin.video.youtube/channel/" + channel + "/live/"
            else:
                url = "plugin://plugin.video.youtube/channel/" + channel + "/"

            xbmcplugin.addDirectoryItem(_handle, url, list_item, isFolder=True)


    xbmcplugin.addDirectoryItem(_handle, '{0}?action=addchan&folder={1}'.format(addon_url, folder), xbmcgui.ListItem(label='Add Channel'), isFolder=False)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(_handle)


def add_category():

    try:

        text = input(str='Add Category')

        data = r_json('favs.json')

        data[text] = []

        w_json('favs.json', data)

        xbmc.executebuiltin('Container.Refresh')

    except:
        pass


def del_category(cat):

    try:

        data = r_json('favs.json')

        data.pop(cat, None)

        w_json('favs.json', data)

        xbmc.executebuiltin('Container.Refresh')

    except:
        pass



def ren_category(cat):

    try:

        data = r_json('favs.json')

        text = input(str='Rename Category')

        data[text] = data.pop(cat)

        w_json('favs.json', data)

        xbmc.executebuiltin('Container.Refresh')

    except:
        pass


def add_channel(folder):

    try:

        text = input(str='Add Channel')
        text = re.sub(' ', '+', text)

        pDialog = xbmcgui.DialogProgress()
        pDialog.create('', 'Searching...')

        url = 'https://www.youtube.com/results?search_query=' + text + '&sp=EgIQAg%253D%253D'

        res = reqPage(url)

        soup = BeautifulSoup(res, 'html.parser')

        select = soup.select('script')

        pDialog.update(25, 'Searching...')

        for scr in select:
            if 'responseContext' in str(scr):
                match = scr.text
                w_json('test.json', match)

        pDialog.update(50, 'Searching...')

        listChannels = []
        dict = []
        iconImages = []

        pattern = re.findall('window\[\"ytInitialData\"\] = (.*?\"adSafetyReason\":{}});', match)[0]

        w_json('test.json', pattern)
        js = json.loads(pattern)
        unpacked = js['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

        pDialog.update(75, 'Searching...')

        for un in unpacked:
            try:

                cid = un['channelRenderer']['channelId']
                title = un['channelRenderer']['title']['simpleText']
                thumb = un['channelRenderer']['thumbnail']['thumbnails'][0]['url']

                listChannels.append(title)
                iconImages.append(thumb)
                dict.append(cid)

            except:
                # basically youtube disregards the channels filter and shows videos anyways, so catch the error.
                pass

        dialog = xbmcgui.Dialog()
        ret = dialog.select('Choose something', listChannels)

        thumb = iconImages[ret]
        thumb = re.sub('//', 'https://', thumb)

        channel = dict[ret]
        channel = str(channel)

        title = list(listChannels)[ret]
        title = codecs.encode(title, 'unicode-escape')

        data = r_json('favs.json')

        data[folder].append({title: {}})

        w_json('favs.json', data)

        for each in data[folder]:

            for i, x in each.items():

                if title in i:
                    x.update({"channel": channel, "thumb": thumb})

        w_json('favs.json', data)

        xbmc.executebuiltin('Container.Refresh')

    except:
        pass


def del_channel(folder, title):

    data = r_json('favs.json')

    title = title.replace('/', '\\')

    for each in data[folder]:

        for i, x in each.items():

            if title == i:
                del each[i]

    w_json('favs.json', data)

    xbmc.executebuiltin('Container.Refresh')


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'channels':
            list_channels(params['folder'])
        if params['action'] == 'addcat':
            add_category()
        if params['action'] == 'delcat':
            del_category(params['cat'])
        if params['action'] == 'addchan':
            add_channel(params['folder'])
        if params['action'] == 'delchan':
            del_channel(params['folder'], params['title'])
        if params['action'] == 'rencat':
            ren_category(params['cat'])
        elif params['action'] == 'play':
            play_video(params['video'])
    else:
        main()
    
if __name__ == '__main__':
    router(sys.argv[2][1:])

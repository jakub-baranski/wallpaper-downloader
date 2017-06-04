import json
import os

import requests
from bs4 import BeautifulSoup

# TODO: Add overwriting settings by command line arguments. Allow for stating search phrase


class ImproperlyConfigured(LookupError):
    pass


class WallpaperGetter:
    settings = {
        "url_base": "https://alpha.wallhaven.cc/",
        "categories": {
            "general": True,
            "anime": False,
            "people": True
        },
        "sfw": True,
        "nsfw": False,
        "resolution": "1920x1080",
        "sorting": "random"
    }

    def __init__(self) -> None:
        with open('settings.json', 'r') as file:
            user_settings = json.loads(file.read())
            if user_settings['url_base'][-1] != '/':
                self.settings['url_base'] += '/'
            for setting in user_settings:
                self.settings[setting] = user_settings[setting]

    def get_categories_representation(self):
        categories = self.settings['categories']
        try:
            return '{}{}{}'.format(
                int(categories['general']),
                int(categories['anime']),
                int(categories['people'])
            )
        except ValueError as e:
            raise ImproperlyConfigured('\'{}\' is not a valid boolean value'.format(e.args[0].split('\'')[1]))

    def get_purity_representation(self):
        try:
            return '{}{}0'.format(int(self.settings['sfw']), int(self.settings['nsfw']))
        except ValueError as e:
            print(e.args)
            raise ImproperlyConfigured('\'{}\' is not a valid boolean value'.format(e.args[0].split('\'')[1]))

    def compose_search_query(self):
        return '{}search?q=&search_image=&categories={}&purity={}&resolution={}&sorting={}'.format(
            self.settings['url_base'],
            self.get_categories_representation(),
            self.get_purity_representation(),
            self.settings['resolution'],
            self.settings['sorting'])

    def get_html(self):
        return requests.get(self.compose_search_query())

    def get_wallpapers_id(self):
        soup = BeautifulSoup(self.get_html().content, "html.parser")
        figure = soup.find('figure', class_='thumb')
        return figure.attrs['data-wallpaper-id']

    def download_random_wallpaper(self):
        random_id = self.get_wallpapers_id()
        for extension in ['jpg', 'png']:
            url = "https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.{}".format(random_id, extension)
            response = requests.get(url)
            if response.status_code == 200:
                with open('getter_{}.{}'.format(random_id, extension), 'wb') as handler:
                    handler.write(response.content)
                    return os.path.abspath(handler.name)

    def set_wallpaper(self):
        # TODO: Make it work for other systems too
        os.system(
            "gsettings set org.gnome.desktop.background picture-uri file://{}".format(self.download_random_wallpaper()))


getter = WallpaperGetter()
getter.set_wallpaper()

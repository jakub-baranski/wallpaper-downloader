import argparse
import json
import logging
import os
import sys

import requests
from bs4 import BeautifulSoup


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
        "sketchy": False,
        "resolution": ["1920x1080"],
        "sorting": "random",
        "keep_wallpapers": 3
    }

    def __init__(self, search_query='') -> None:
        if search_query != '':
            logging.info('Got search query "{}"'.format(search_query))
        self.search_query = search_query
        try:
            logging.info('Attempting to load user settings... ')
            with open('settings.json', 'r') as file:
                user_settings = json.loads(file.read())
                if user_settings['url_base'][-1] != '/':
                    self.settings['url_base'] += '/'
                for setting in user_settings:
                    self.settings[setting] = user_settings[setting]
                logging.info('DONE')
        except FileNotFoundError:
            logging.info('settings.json not found. Using default settings instead.')

    def get_categories_representation(self):
        categories = self.settings['categories']
        try:
            logging.info('Setting categories')
            return '{}{}{}'.format(
                int(categories['general']),
                int(categories['anime']),
                int(categories['people'])
            )
        except ValueError as e:
            raise ImproperlyConfigured('\'{}\' is not a valid boolean value'.format(e.args[0].split('\'')[1]))

    def get_purity_representation(self):
        try:
            logging.info('Setting purity')
            return '{}{}0'.format(int(self.settings['sfw']), int(self.settings['sketchy']))
        except ValueError as e:
            raise ImproperlyConfigured('\'{}\' is not a valid boolean value'.format(e.args[0].split('\'')[1]))

    def compose_search_query(self):
        logging.info('Composing search query string.')
        return '{}search?q={}&search_image=&categories={}&purity={}&resolutions={}&sorting={}'.format(
            self.settings['url_base'],
            self.search_query,
            self.get_categories_representation(),
            self.get_purity_representation(),
            ','.join(self.settings['resolution']),
            self.settings['sorting'])

    def get_wallpapers_id(self):
        response = requests.get(self.compose_search_query())
        page = response.content
        soup = BeautifulSoup(page, "html.parser")
        logging.info('Getting random wallpaper id... ')
        figures = soup.find('figure', class_='thumb')
        if figures:
            wallpaper_id = figures.attrs['data-wallpaper-id']
            logging.info('Got id: {}'.format(wallpaper_id))
            return wallpaper_id
        logging.warning('\n-404-: No wallpapers found for search phrase \'{}\''.format(self.search_query))
        sys.exit(0)

    def download_random_wallpaper(self):
        random_id = self.get_wallpapers_id()
        logging.info('Downloading wallpaper.')
        for extension in ['jpg', 'png']:
            logging.info('Trying extension: {}... '.format(extension))
            url = "https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.{}".format(random_id, extension)
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logging.info('SUCCESS')
                self.create_wallpaper_directory()
                name = 'downloads/getter_{}.{}'.format(random_id, extension)
                logging.info('Saving as {}... '.format(name))
                with open(name, 'wb') as handler:
                    handler.write(response.content)
                    logging.info('DONE.')
                    self.purge_wallpapers()
                    return os.path.abspath(handler.name)
            logging.info('FAILED')

    def create_wallpaper_directory(self) -> None:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

    def purge_wallpapers(self) -> None:
        keep = self.settings['keep_wallpapers']
        files = os.listdir('downloads')
        if 0 < keep < len(files):
            logging.info('Purging previously downloaded wallpapers. Keeping recent {}.'.format(keep))
            files.sort(key=lambda file: os.path.getmtime('downloads/{}'.format(file)), reverse=True)
            for i in range(keep, len(files)):
                os.remove('downloads/{}'.format(files[i]))

    def set_wallpaper(self):
        # TODO: Make it work for other systems too
        logging.info('Setting wallpaper.')
        os.system(
            "gsettings set org.gnome.desktop.background picture-uri file://{}".format(self.download_random_wallpaper()))
        logging.info('FIN.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    parser.add_argument(
        '-s', '--search',
        help='Search for specific wallpaper with search query',
        action='append', dest='search'
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    getter = WallpaperGetter(search_query=' '.join(args.search) if args.search else '')
    getter.set_wallpaper()

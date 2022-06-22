import random

from translation.conftest import HexFetcher

from rics.translation import Translator
from rics.translation.fetching import MultiFetcher
from rics.utility.logs import basic_config, logging

basic_config(level=logging.DEBUG)

dvdrental = Translator.from_config("tests/translation/dvdrental/config.toml")._fetcher
dvdrental2 = Translator.from_config("tests/translation/dvdrental/config.toml")._fetcher
imdb = Translator.from_config("tests/translation/config.imdb.toml")._fetcher
imdb2 = Translator.from_config("tests/translation/config.imdb.toml")._fetcher
hexf = HexFetcher()

order = [dvdrental, dvdrental2, imdb, imdb2, hexf]
random.shuffle(order)

mf = MultiFetcher(*order, max_workers=5)

mf.fetch_all()

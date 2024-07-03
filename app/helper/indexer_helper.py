import json

from app.utils import StringUtils, ExceptionUtils
from app.utils.commons import singleton
from app.helper import DbHelper
from app.helper.indexer_conf import IndexerConf


@singleton
class IndexerHelper:
    _indexers = []

    def __init__(self):
        self.init_config()

    def init_config(self):
        self._indexers.clear()
        try:
            for inexer in DbHelper().get_indexer_custom_site():
                self._indexers.append(json.loads(inexer.INDEXER))
        except Exception as err:
            ExceptionUtils.exception_traceback(err)

    def get_indexer(self,
                    url,
                    siteid=None,
                    cookie=None,
                    name=None,
                    rule=None,
                    public=None,
                    proxy=False,
                    parser=None,
                    ua=None,
                    render=None,
                    language=None,
                    pri=None,
                    apikey=None,
                    authorization=None):
        self.init_config()
        if not url:
            return None
        for indexer in self._indexers:
            if not indexer.get("domain"):
                continue
            if StringUtils.url_equal(indexer.get("domain"), url):
                return IndexerConf(siteid=siteid,
                                   datas=indexer,
                                   cookie=cookie,
                                   name=name,
                                   rule=rule,
                                   public=public,
                                   proxy=proxy,
                                   parser=parser,
                                   ua=ua,
                                   render=render,
                                   builtin=True,
                                   language=language,
                                   pri=pri,
                                   apikey=apikey,
                                   authorization=authorization)
        return None
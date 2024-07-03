import xml.dom.minidom

from lxml import etree
from app.db import MainDb, DbPersist
from app.db.models import RSSTORRENTS
from app.utils import RssTitleUtils, StringUtils, RequestUtils, ExceptionUtils, DomUtils
from config import Config
from urllib.parse import urljoin
import log

class RssHelper:
    _db = MainDb()

    """
      RSS帮助类，解析RSS报文、获取RSS地址等
      """
    # 各站点RSS链接获取配置
    rss_link_conf = {
        "default": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "hares.top": {
            "xpath": "//*[@id='layui-layer100001']/div[2]/div/p[4]/a/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "et8.org": {
            "xpath": "//*[@id='outer']/table/tbody/tr/td/table/tbody/tr/td/a[2]/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "pttime.org": {
            "xpath": "//*[@id='outer']/table/tbody/tr/td/table/tbody/tr/td/text()[5]",
            "url": "getrss.php",
            "params": {
                "showrows": 10,
                "inclbookmarked": 0,
                "itemsmalldescr": 1
            }
        },
        "ourbits.club": {
            "xpath": "//a[@class='gen_rsslink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "totheglory.im": {
            "xpath": "//textarea/text()",
            "url": "rsstools.php?c51=51&c52=52&c53=53&c54=54&c108=108&c109=109&c62=62&c63=63&c67=67&c69=69&c70=70&c73=73&c76=76&c75=75&c74=74&c87=87&c88=88&c99=99&c90=90&c58=58&c103=103&c101=101&c60=60",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "monikadesign.uk": {
            "xpath": "//a/@href",
            "url": "rss",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "zhuque.in": {
            "xpath": "//a/@href",
            "url": "user/rss",
            "render": True,
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
            }
        },
        "hdchina.org": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "rsscart": 0
            }
        },
        "audiences.me": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "torrent_type": 1,
                "exp": 180
            }
        },
        "shadowflow.org": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "paid": 0,
                "search_mode": 0,
                "showrows": 30
            }
        },
        "hddolby.com": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "exp": 180
            }
        },
        "hdhome.org": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "exp": 180
            }
        },
        "pthome.net": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "exp": 180
            }
        },
        "ptsbao.club": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "size": 0
            }
        },
        "leaves.red": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 0,
                "paid": 2
            }
        },
        "hdtime.org": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 0,
            }
        },
        "m-team.io": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "showrows": 50,
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "https": 1
            }
        },
        "u2.dmhy.org": {
            "xpath": "//a[@class='faqlink']/@href",
            "url": "getrss.php",
            "params": {
                "inclbookmarked": 0,
                "itemsmalldescr": 1,
                "showrows": 50,
                "search_mode": 1,
                "inclautochecked": 1,
                "trackerssl": 1
            }
        },
    }

    def get_rss_link(self, url, cookie, proxy: bool = False):
        """
        获取站点rss地址
        :param url: 站点地址
        :param cookie: 站点cookie
        :param ua: 站点ua
        :param proxy: 是否使用代理
        :return: rss地址、错误信息
        """
        try:
            # 获取站点域名
            domain = StringUtils.get_url_domain(url)
            # 获取配置
            site_conf = self.rss_link_conf.get(domain) or self.rss_link_conf.get("default")
            # RSS地址
            rss_url = urljoin(url, site_conf.get("url"))
            # RSS请求参数
            rss_params = site_conf.get("params")
            # 请求RSS页面
            if site_conf.get("render"):
                html_text = RequestUtils(
                    cookies=cookie,
                    proxies=proxy
                ).get(url=rss_url, data=rss_params)
            else:
                res = RequestUtils(
                    cookies=cookie,
                    timeout=60,
                    proxies=proxy
                ).post_res(url=rss_url, data=rss_params)
                if res:
                    html_text = res.text
                elif res is not None:
                    return "", f"获取 {url} RSS链接失败，错误码：{res.status_code}，错误原因：{res.reason}"
                else:
                    return "", f"获取RSS链接失败：无法连接 {url} "
            # 解析HTML
            html = etree.HTML(html_text)
            if html:
                rss_link = html.xpath(site_conf.get("xpath"))
                if rss_link:
                    return str(rss_link[-1]), ""
            return "", f"获取RSS链接失败：{url}"
        except Exception as e:
            return "", f"获取 {url} RSS链接失败：{str(e)}"

    @staticmethod
    def parse_rssxml(url, proxy=False):
        """
        解析RSS订阅URL，获取RSS中的种子信息
        :param url: RSS地址
        :param proxy: 是否使用代理
        :return: 种子信息列表，如为None代表Rss过期
        """
        _special_title_sites = {
            'pt.keepfrds.com': RssTitleUtils.keepfriends_title
        }

        _rss_expired_msg = [
            "RSS 链接已过期, 您需要获得一个新的!",
            "RSS Link has expired, You need to get a new one!"
        ]

        # 开始处理
        ret_array = []
        if not url:
            return []
        site_domain = StringUtils.get_url_domain(url)
        try:
            ret = RequestUtils(proxies=Config().get_proxies() if proxy else None).get_res(url)
            if not ret:
                return []
            ret.encoding = ret.apparent_encoding
        except Exception as e2:
            ExceptionUtils.exception_traceback(e2)
            return []
        if ret:
            ret_xml = ret.text
            try:
                # 解析XML
                dom_tree = xml.dom.minidom.parseString(ret_xml)
                rootNode = dom_tree.documentElement
                items = rootNode.getElementsByTagName("item")
                for item in items:
                    try:
                        # 标题
                        title = DomUtils.tag_value(item, "title", default="")
                        if not title:
                            continue
                        # 标题特殊处理
                        if site_domain and site_domain in _special_title_sites:
                            title = _special_title_sites.get(site_domain)(title)
                        # 描述
                        description = DomUtils.tag_value(item, "description", default="")
                        # 种子页面
                        link = DomUtils.tag_value(item, "link", default="")
                        # 种子链接
                        enclosure = DomUtils.tag_value(item, "enclosure", "url", default="")
                        if not enclosure and not link:
                            continue
                        # 部分RSS只有link没有enclosure
                        if not enclosure and link:
                            enclosure = link
                            link = None
                        # 大小
                        size = DomUtils.tag_value(item, "enclosure", "length", default=0)
                        if size and str(size).isdigit():
                            size = int(size)
                        else:
                            size = 0
                        # 发布日期
                        pubdate = DomUtils.tag_value(item, "pubDate", default="")
                        if pubdate:
                            # 转换为时间
                            pubdate = StringUtils.get_time_stamp(pubdate)
                        # 返回对象
                        tmp_dict = {'title': title,
                                    'enclosure': enclosure,
                                    'size': size,
                                    'description': description,
                                    'link': link,
                                    'pubdate': pubdate}
                        ret_array.append(tmp_dict)
                    except Exception as e1:
                        ExceptionUtils.exception_traceback(e1)
                        continue
            except Exception as e2:
                # RSS过期 观众RSS 链接已过期，您需要获得一个新的！  pthome RSS Link has expired, You need to get a new one!
                if ret_xml in _rss_expired_msg:
                    return None
                ExceptionUtils.exception_traceback(e2)
        return ret_array

    @DbPersist(_db)
    def insert_rss_torrents(self, media_info):
        """
        将RSS的记录插入数据库
        """
        self._db.insert(
            RSSTORRENTS(
                TORRENT_NAME=media_info.org_string,
                ENCLOSURE=media_info.enclosure,
                TYPE=media_info.type.value,
                TITLE=media_info.title,
                YEAR=media_info.year,
                SEASON=media_info.get_season_string(),
                EPISODE=media_info.get_episode_string()
            ))

    def is_rssd_by_enclosure(self, enclosure):
        """
        查询RSS是否处理过，根据下载链接
        """
        if not enclosure:
            return True
        if self._db.query(RSSTORRENTS).filter(RSSTORRENTS.ENCLOSURE == enclosure).count() > 0:
            return True
        else:
            return False

    def is_rssd_by_simple(self, torrent_name, enclosure):
        """
        查询RSS是否处理过，根据名称
        """
        if not torrent_name and not enclosure:
            return True
        if enclosure:
            ret = self._db.query(RSSTORRENTS).filter(RSSTORRENTS.ENCLOSURE == enclosure).count()
        else:
            ret = self._db.query(RSSTORRENTS).filter(RSSTORRENTS.TORRENT_NAME == torrent_name).count()
        return True if ret > 0 else False

    @DbPersist(_db)
    def simple_insert_rss_torrents(self, title, enclosure):
        """
        将RSS的记录插入数据库
        """
        self._db.insert(
            RSSTORRENTS(
                TORRENT_NAME=title,
                ENCLOSURE=enclosure
            ))

    @DbPersist(_db)
    def simple_delete_rss_torrents(self, title, enclosure=None):
        """
        删除RSS的记录
        """
        if enclosure:
            self._db.query(RSSTORRENTS).filter(RSSTORRENTS.TORRENT_NAME == title,
                                               RSSTORRENTS.ENCLOSURE == enclosure).delete()
        else:
            self._db.query(RSSTORRENTS).filter(RSSTORRENTS.TORRENT_NAME == title).delete()

    @DbPersist(_db)
    def truncate_rss_history(self):
        """
        清空RSS历史记录
        """
        self._db.query(RSSTORRENTS).delete()

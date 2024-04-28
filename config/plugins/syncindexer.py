import json
import pytz

from threading import Event
from config import Config
from app.helper import DbHelper
from datetime import datetime, timedelta
from app.plugins.modules._base import _IPluginModule
from app.utils import RequestUtils, SchedulerUtils, StringUtils, JsonUtils
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.types import EventType
from app.plugins import EventHandler
from app.sites.sites import Sites
from web.backend.user import User
from jinja2 import Template


class SyncIndexer(_IPluginModule):
    # 插件名称
    module_name = "同步索引规则"
    # 插件描述
    module_desc = "可根据配置站点自动获取已适配的索引规则和刷流规则。可以配合 '自定义索引器' 和 '自定义刷流规则' 插件使用。"
    # 插件图标
    module_icon = "syncindexer.png"
    # 主题色
    module_color = "#02C4E0"
    # 插件版本
    module_version = "1.7"
    # 插件作者
    module_author = "mattoid"
    # 作者主页
    author_url = "https://github.com/Mattoids"
    # 插件配置项ID前缀
    module_config_prefix = "syncindexer_"
    # 加载顺序
    module_order = 24
    # 可使用的用户级别
    auth_level = 1
    # 退出事件
    _event = Event()

    # 私有属性
    _scheduler = None
    _gitee_url = "https://gitee.com/Mattoid/nas-tools-plugin/raw/master"
    _github_url = "https://github.com/Mattoids/nas-tools-plugin/raw/master"

    _enable = False
    _gitee_switch = 0
    _refresh = False
    _onlyonce = False
    _cron = ""

    @staticmethod
    def get_fields():
        return [
            # 同一板块
            {
                'type': 'div',
                'content': [
                    # 同一行
                    [
                        {
                            'title': '开启自动同步',
                            'required': "required",
                            'tooltip': '开启同步后将会从作者github仓库中同步站点的索引数据和站点的刷流数据，达到支持更多的站点的目的。',
                            'type': 'switch',
                            'id': 'enable'
                        },
                        {
                            'title': '使用gitee仓库',
                            'required': "required",
                            'tooltip': '如果因为网络原因无法使用github仓库同步的情况下，可以开启该选项从国内公开仓库获取数据。',
                            'type': 'switch',
                            'id': 'gitee_switch'
                        },
                        {
                            'title': '刷新所有站点',
                            'required': "required",
                            'tooltip': '强制刷新所有站点将会清除同步历史，然后对现有配置的站点进行重新同步。',
                            'type': 'switch',
                            'id': 'refresh'
                        },
                        {
                            'title': '立即运行一次',
                            'required': "required",
                            'tooltip': '开启将会直接运行一次同步任务，并且自动关闭该选项。',
                            'type': 'switch',
                            'id': 'onlyonce'
                        }
                    ],
                    [
                        {
                            'title': '同步周期',
                            'required': "",
                            'tooltip': '定时同步作者更新的站点索引和刷流信息',
                            'type': 'text',
                            'content': [
                                {
                                    'id': 'cron',
                                    'placeholder': '0 0 0 ? *',
                                }
                            ]
                        },
                    ]
                ]
            }
        ]

    def get_page(self):
        """
        插件的额外页面，返回页面标题和页面内容
        :return: 标题，页面内容，确定按钮响应函数
        """
        results = self.get_history()
        template = """
          <div class="table-responsive table-modal-body">
            <table class="table table-vcenter card-table table-hover table-striped">
              <thead>
              <tr>
                <th>站点</th>
                <th>同步类型</th>
                <th>状态</th>
                <th>描述</th>
                <th>同步时间</th>
              </tr>
              </thead>
              <tbody>
              {% if HistoryCount > 0 %}
                {% for Item in SyncIndexerHistory %}
                  <tr id="douban_history_{{ Item.site }}">
                    <td>
                      <div>{{ Item.site }}</div>
                    </td>
                    <td>
                      <div>{{ Item.type }}</div>
                    </td>
                    <td>
                      {{ Item.status }}
                    </td>
                    <td>
                      {{ Item.message }}
                    </td>
                    <td>
                      {{ Item.time }}
                    </td>
                  </tr>
                {% endfor %}
              {% else %}
                <tr>
                  <td colspan="6" align="center">没有数据</td>
                </tr>
              {% endif %}
              </tbody>
            </table>
          </div>
        """
        return "同步历史", Template(template).render(HistoryCount=len(results),
                                                     SyncIndexerHistory=results), None

    @staticmethod
    def get_script():
        pass

    def init_config(self, config=None):
        # 读取配置
        if config:
            self._enable = config.get("enable")
            self._gitee_switch = config.get("gitee_switch")
            self._refresh = config.get("refresh")
            self._onlyonce = config.get("onlyonce")
            self._cron = config.get("cron")

        if self._enable:
            # 定时服务
            self._scheduler = BackgroundScheduler(timezone=Config().get_timezone())

            if self._onlyonce:
                self._onlyonce = False
                self.info(f"索引同步，立即运行一次")
                self._scheduler.add_job(self.__update_site_indexer, 'date',
                                        run_date=datetime.now(tz=pytz.timezone(Config().get_timezone())) + timedelta(
                                            seconds=3))

                self.update_config({
                    "enable": self._enable,
                    "gitee_switch": self._gitee_switch,
                    "refresh": self._refresh,
                    "onlyonce": self._onlyonce,
                    "cron": self._cron
                })

            # 周期运行
            if self._cron:
                self.info(f"自动同步索引规则，周期：{self._cron}")
                SchedulerUtils.start_job(scheduler=self._scheduler,
                                         func=self.__update_site_indexer,
                                         func_desc="同步索引推责",
                                         cron=str(self._cron))

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()


    def get_state(self):
        return self._enable and self._cron

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            print(str(e))

    def __update_site_indexer(self):
        for site in Sites().get_sites():
            site_url = site.get("signurl")
            site_domain = StringUtils.get_url_domain(site_url)

            self.__update_indexer(site_url=site_url, site_domain=site_domain)
            self.__update_brush(site_url=site_url, site_domain=site_domain)

        return True

    def __update_indexer(self, site_url, site_domain):
        if not self._refresh and not User().get_indexer(url=site_url):
            self.__insert_history(site_domain, "indexer", False, "未开启刷新所有站点，本次不更新!")
            return True

        url = f"{self._gitee_url if self._gitee_switch else self._github_url}/sites/{site_domain}.json"

        result = RequestUtils(timeout=5, proxies=Config().get_proxies()).get_res(url)

        if result.status_code == 404:
            self.__insert_history(site_domain, "indexer", False, "站点索引规则不存在，请联系作者进行适配!")
            return False

        if result.status_code == 200:
            if not DbHelper().get_indexer_custom_site(site_url):
                DbHelper().insert_indexer_custom_site(site_url, json.dumps(result.json()))
            elif self._refresh:
                DbHelper().insert_indexer_custom_site(site_url, json.dumps(result.json()))
        else:
            self.__insert_history(site_domain, "indexer", False, result.status_code)
            return False

        self.__insert_history(site_domain, "indexer", True, "成功")
        return True

    def __update_brush(self, site_url, site_domain):
        if not self._refresh and site_domain not in User().get_brush_conf():
            self.__insert_history(site_domain, "brush", False, "未开启刷新所有站点，本次不更新!")
            return True

        url = f"{self._gitee_url if self._gitee_switch else self._github_url}/sites/brush/{site_domain}.json"

        result = RequestUtils(timeout=5, proxies=Config().get_proxies()).get_res(url)

        if result.status_code == 404:
            self.__insert_history(site_domain, "brush", False, "站点刷流规则不存在，请联系作者进行适配!")
            return False

        if result.status_code == 200:
            config = Config().get_config()
            site_brush = json.loads(config['laboratory']['site_brush'] or "{}")
            if site_domain not in site_brush:
                site_brush[site_domain] = json.loads(result.content)
            elif self._refresh:
                site_brush[site_domain] = json.loads(result.content)

            brush = json.dumps(JsonUtils.json_serializable(site_brush))
            config['laboratory']['site_brush'] = brush
            Config().save_config(config)

            self.update_config({"site_brush": brush}, "CustomBrush")
        else:
            self.__insert_history(site_domain, "brush", False, result.status_code)
            return False

        self.__insert_history(site_domain, "brush", True, "成功")
        return True

    def __insert_history(self, site_url, type, status, message):
        value = {
            "site": site_url,
            "type": type,
            "status": "成功" if status else "失败",
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.delete_history(site_url)
        self.history(key=site_url, value=value)

    @staticmethod
    def get_command():
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return {
            "cmd": "/ptc",
            "event": EventType.SiteEdit,
            "desc": "同步站点信息",
            "category": "站点",
            "data": {}
        }

    @EventHandler.register(EventType.SiteEdit)
    def sync_cookiecloud(self, event=None):
        self.__update_site_indexer()
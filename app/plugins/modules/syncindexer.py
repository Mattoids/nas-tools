import os
import importlib

from config import Config
from datetime import datetime
from app.utils import RequestUtils
from app.plugins.modules._base import _IPluginModule
from jinja2 import Template

class SyncIndexer(_IPluginModule):
    # 插件名称
    module_name = "同步索引规则"
    # 插件描述
    module_desc = "用于同步 MoviePilot 的规则文件，达到增强索引器的功能。(每次同步后重启 nas-tools 生效)"
    # 插件图标
    module_icon = "syncindexer.png"
    # 主题色
    module_color = "#02C4E0"
    # 插件版本
    module_version = "1.2"
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

    # 私有属性
    _enable = False
    _sync_type = 0
    _url = ""

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
                            'tooltip': '将从数据源处获取站点索引规则，对 user.sites.bin 文件进行修改',
                            'type': 'switch',
                            'id': 'enable'
                        }
                    ],
                    [
                        {
                            'title': '同步源',
                            'required': "required",
                            'tooltip': '选择使用一种同步源来同步 user.sites.bin 文件内容',
                            'type': 'select',
                            'content': [
                                {
                                    'id': 'sync_type',
                                    'options': {
                                        '0': '回滚致原版',
                                        '1': '憨憨',
                                        '2': '自定义'
                                    },
                                    'default': '0',
                                    'onchange': 'SyncIndexer_type_change(this)'
                                }
                            ]
                        }
                    ],
                    [
                        {
                            'title': '源地址',
                            'required': False,
                            'tooltip': '填写 user.sites.bin 文件的下载链接',
                            'type': 'text',
                            'readonly': True,
                            'content': [
                                {
                                    'id': 'url',
                                    'placeholder': '',
                                }
                            ]
                        }
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
                <th>序号</th>
                <th>同步类型</th>
                <th>状态</th>
                <th>描述</th>
                <th>同步时间</th>
              </tr>
              </thead>
              <tbody>
              {% if HistoryCount > 0 %}
                {% for Item in SyncIndexerHistory %}
                  <tr id="douban_history_{{ Item.id }}">
                    <td class="w-5">
                      {{ Item.id }}
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
        return """            
              // 同步方式切换
              function SyncIndexer_type_change(obj){
                if ($(obj).val() == '0') {
                    $('#syncindexer_url').val('https://raw.githubusercontent.com/Mattoids/nas-tools-plugin/master/sites/user.sites.bin');
                    $('#syncindexer_url').prop("readonly", false);
                } else if ($(obj).val() == '1') {
                    $('#syncindexer_url').val('https://hhanclub.top/user.sites.bin');
                    $('#syncindexer_url').prop("readonly", true);
                } else {
                    $('#syncindexer_url').val('');
                    $('#syncindexer_url').prop("readonly", true);
                }
              }
              
              $(function(){
                    $('#syncindexer_url').val('https://raw.githubusercontent.com/Mattoids/nas-tools-plugin/master/sites/user.sites.bin');
                    $('#syncindexer_url').prop("readonly", true);
              });
        """

    def init_config(self, config=None):
        # 读取配置
        if config:
            self._enable = config.get("enable")
            self._sync_type = config.get("sync_type")
            self._url = config.get("url")
        if self._enable:
            self._enable = False
            self.update_config({
                "url": self._url,
                "sync_type": self._sync_type,
                "enable": self._enable,
            })

            self.__update_history(config)

    def get_state(self):
        return self._enable

    def stop_service(self):
        """
        退出插件
        """
        pass

    def __update_history(self, config=None):
        """
        插入历史记录
        """
        result, message = self.__update_user_sites_bin(config.get("url"))

        id = len(self.get_history()) + 1 or 1

        value = {
            "id": id,
            "type": "MoviePilot" if config.get("sync_type") == 0 else "自定义",
            "status": "成功" if result else "失败",
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.history(key=id, value=value)

    def __update_user_sites_bin(self, url=None):
        if not url:
            return False, "url不存在"

        try:
            path = importlib.resources.files('web.backend')
            file = os.path.join(path, "user.sites.bin")

            file_data = RequestUtils(timeout=5, proxies=Config().get_proxies()).get_res(url)

            if not file_data or not file_data.content:
                return False, "源地址出错，请检查源是否可以正常打开"

            open(file, "wb").write(file_data.content)

        except Exception as err:
            print(err)
            return False, err

        return True, "成功"
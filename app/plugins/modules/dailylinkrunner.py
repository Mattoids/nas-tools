import requests
import datetime
from app.plugins.modules._base import _IPluginModule
from app.helper import DbHelper
from jinja2 import Template

class DailyLinkRunner(_IPluginModule):
    # 插件的基本信息
    module_name = "定时每日链接访问器"
    module_desc = "在每天的指定时间访问自定义链接"
    module_icon = "link.png"
    module_color = "#FF5733"
    module_version = "1.2"
    module_author = "maxgt"
    author_url = "https://github.com/GTian28"
    module_config_prefix = "dailylinkrunner_"
    module_order = 18
    auth_level = 1

    _config = {}
    _links = []  # 存放用户添加的链接
    _run_time = None

    @staticmethod
    def get_fields():
        return [
            {
                'type': 'div',
                'content': [
                    [
                        # "添加"按钮
                        {
                            'title': '添加',
                            'type': 'button',
                            'value': '添加',
                            'onclick': 'add_link()'
                        },
                        # "立即访问一次"按钮
                        {
                            'title': '立即访问一次',
                            'type': 'button',
                            'value': '立即访问一次',
                            'onclick': 'run_links_now()'
                        }
                    ]
                ]
            },
            {
                'type': 'div',
                'content': [
                    [
                        {
                            'title': '链接',
                            'required': "required",
                            'tooltip': "请填写要定时访问的链接",
                            'type': 'text',
                            'content': [
                                {
                                    'id': 'link',
                                    'placeholder': '要访问的链接',
                                }
                            ]
                        },
                    ],
                    [
                        {
                            'title': '每日运行时间',
                            'required': "required",
                            'tooltip': "每天执行任务的时间",
                            'type': 'time',
                            'content': [
                                {
                                    'id': 'runtime',
                                    'placeholder': '例如 12:35',
                                }
                            ]
                        },
                    ]
                ]
            }
        ]

    @staticmethod
    def get_script():
        return """
        var links = [];

        function add_link() {
            var link = $("#dailylinkrunner_link").val();
            var runtime = $("#dailylinkrunner_runtime").val();
            
            if (link) {
                links.push(link);

                // 添加到一个显示列表中，让用户知道他们添加了哪些链接
                var linkList = $("#dailylinkrunner_linkList");
                if (!linkList.length) {
                    $('<ul id="dailylinkrunner_linkList"></ul>').insertAfter("#dailylinkrunner_link");
                }
                $("#dailylinkrunner_linkList").append("<li>" + link + "</li>");

                // 清空输入框，以便用户可以继续添加其他链接
                $("#dailylinkrunner_link").val("");
            }
        }

        function run_links_now() {
            if (links.length > 0) {
                links.forEach(function(link) {
                    // 这里我们简单地使用GET请求，你可以根据需要调整
                    $.get(link)
                    .done(function() {
                        console.log("成功访问链接: " + link);
                    })
                    .fail(function() {
                        console.error("访问链接" + link + "时出错");
                    });
                });
            } else {
                alert("请先添加至少一个链接!");
            }
        }
        """

    def init_config(self, config=None):
        self.info(f"初始化{config}")

        # 从配置中提取链接和运行时间
        links = config.get("links", [])
        runtime = config.get("runtime", "")

        # 如果存在链接和运行时间，将它们保存到数据库
        if links and runtime:
            # 假设DbHelper有一个方法来保存或更新我们的配置
            DbHelper().save_daily_link_runner_config(links, runtime)

        # 更新内部配置以反映这些变化
        self.update_config({
            "links": links,
            "runtime": runtime
        })


    def check_run_time(self):
        current_time = datetime.datetime.now().time()
        run_hour, run_minute = map(int, self._run_time.split(':'))
        run_time = datetime.time(run_hour, run_minute)

        # 检查是否为指定运行时间
        if current_time == run_time:
            self.run_links_now()

    def run_link(self, link):
        # 根据传入的链接运行
        if link:
            try:
                requests.get(link)
                self.info(f"成功访问链接: {link}")
            except requests.RequestException as e:
                self.error(f"访问链接{link}时出错: {str(e)}")

    def run_links_now(self):
        for link_info in self._links:
            self.run_link(link_info["link"])

    def get_state(self):
        return True

    def stop_service(self):
        pass

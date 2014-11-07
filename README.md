## 数据分析平台

### SETUP

```sh
$ git clone git@github.com:yangwenjing/www.git
$ cd analysis
$ pip install -r requirements.txt
$ ./manage.py syncdb
$ ./manage.py migrate
$ ./manage.py runserver
```


### 开发

所有独立的功能都需要放到一个单独的 App 中

我们使用 `django-south` 管理数据库结构的变更

```sh
$ ./manage.py startapp new_app
$ mv new_app analysis
$ vim settings.py # add 'analysis.new_app' to INSTALLED_APPS
$ ./manage.py schemamigration new_app --initial # 创建空的 migration

$ vim analysis/new_app/models.py
$ ./manage.py schemamigration new_app --auto  # 修改 models 后生成 migration
$ ./manage.py migrate  # 运行 migration
```

### 部署

`deploy` 目录有两个文件，一个是 nginx 的配置文件，一个是 `init.d` 启动脚本。

`init.d` 脚本会使用 `gunicorn` 作为应用容器启动后端进程，`nginx` 做前端代理


#### 部署步骤

```sh
cp deploy/nginx/*.conf /etc/nginx/conf.d
cp deploy/init.d/datacubic /etc/init.d
/etc/init.d/datacubic start
```

#### 升级步骤

```sh
cd /path_to/app/folder
git pull
source ../env/bin/activate
pip install -r requirements  # 如果添加了新的依赖
./manage.py syncdb --migrate  # 同步数据库并且执行migration 脚本
./manage.py collectstatic --noinput  # 收集静态文件
/etc/init.d/datacubic restart  # 重启应用服务器进程
```

#### CRON

需要将 sync_dip 添加到计划任务中去，可以每小时运行一次，导入上一小时的 DIP 任务数据

需要将 compress_table 添加到计划任务中去，每天运行一次

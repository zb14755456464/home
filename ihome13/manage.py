# coding=utf-8


from flask_script import Manager
from ihome import create_app, db
from flask_migrate import Migrate, MigrateCommand

# 通过create_app获取app
app = create_app('development')

# 创建Manager
manager = Manager(app)

# 创建迁移对象
migrate = Migrate(app, db)

# 给manager添加db命令, 以后需要通过python manage.py db init/migrate/upgrade 进行数据库的迁移操作
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
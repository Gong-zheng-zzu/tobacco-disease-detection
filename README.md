文件夹1 里面是APP（其实是用HBuilder X）包装的，然后app里面是全部文件，app-release是精简文件，用来把web包装成APP。逻辑是修改app文件夹的代码，然后再同步到app-release（AI是这么干的，我也不知道具体啥原理。可以看一下app-release-sync这个文件，是当时给AI的提示词）

然后 前后端 文件夹里是运行的代码，drf_test002放的是后端，tobacco放的是前端。下面的是启动命令：
# 1. 进入后端目录
  cd "E:\烟草\前后端\drf_test002"

  # 2. 激活虚拟环境
  .venv\Scripts\activate

  # 3. 确保 MySQL 已启动（数据库: test_db, 用户: root, 密码: 123456）
  #     如果数据库没建，先建库：
  #     mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS test_db DEFAULT CHARSET utf8mb4;"

  # 4. 安装/更新依赖（如果缺包）
  pip install -r requirements.txt

  # 5. 数据库迁移
  python manage.py migrate

  # 6. 启动开发服务器（默认 8000 端口）
  python manage.py runserver 0.0.0.0:8000

  注意事项：
  - 需要本地已安装 MySQL，数据库连接信息在 drf_test002/settings.py:103-115
  - 虚拟环境 .venv 已存在，Python 可直接使用
  - 项目依赖 torch 和 ultralytics（YOLOv8），比较重，确保已安装
  - 如果只是跑接口不需要推理，可以先忽略模型相关报错

  ---
  二、启动前端（Vue 3 + Vite）

  # 1. 进入前端目录
  cd "E:\烟草\前后端\tobacco"

  # 2. 依赖已装好（node_modules 存在），直接启动
  npm run dev

  访问地址：https://localhost:5173 （注意是 HTTPS，Vite 配置了自签名证书）

disease文件夹里的是病虫害检测的训练、预测代码和权重文件，我记得我已经把训练好的权重放在后端文件夹里了
模型部署 文件夹里是缺素的代码，权重也在后端里有

python串口 这个文件夹没用到，因为我们没连上硬件

目标检测图片 文件夹是看模型的预测结果的

剩下的就是数据集了

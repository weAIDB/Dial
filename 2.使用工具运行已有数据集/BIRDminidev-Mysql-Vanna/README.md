# WrenAI 训练流程说明

## 输入数据准备
- **DDL 获取**  
  使用 `get_DDL` 脚本获取数据库的 DDL（数据定义语言）

- **文档数据**  
  使用 `mini_dev_mysql` 数据库中的 `evidence` 字段作为文档输入

## 训练流程
完成上述数据输入后，运行`train_vanna`脚本进行训练

## 结果生成
训练结束后，通过执行 `run_BIRD_on_vanna` 脚本生成 SQL 语句
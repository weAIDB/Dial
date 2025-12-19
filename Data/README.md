-database-sqlite   数据集所用的全部sqlite文件

-migrate.py   将sqlite文件迁移到mysql、postgres数据库

-Extract table.column.py   通过llm识别gold sql里面所用的“表.列”


-dataset.json  根据周乐提供的训练集和验证集合并而得，同时剔除了sql语句不能执行、三个方言答案不一的条目，最终获得1537条数据

-dataset_no_empty.json  剔除数据集sql执行结果为空的条目，共749条

-datasetEX.json   通过baseline筛选出的会出错的数据集，共692条

-true_result_all.json   dataset.json里sql语句执行的结果（mysql、sqlite、pgsql答案完全相同），供与generated_sql对比使用

-true_result_no_empty.json   dataset_no_empty.json里sql语句执行的结果（mysql、sqlite、pgsql答案完全相同），供与generated_sql对比使用

-true_resultEX.json   datasetEX.json里sql语句执行的结果（mysql、sqlite、pgsql答案完全相同），供与generated_sql对比使用
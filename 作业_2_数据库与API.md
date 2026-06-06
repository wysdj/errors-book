错题管理器 — 课后作业（2）


提交方式：直接在【】里填写。下次说"继续错题项目"老师会先看作业。





作业一：理解数据库设计

看了我设计的四张表（errors / knowledge_points / reviews / review_steps），
用你自己的话回答：


为什
么 knowledge_points 要单独一张表，而不是在 errors 表里加几个字段存知识点？ 【因为一个题可以有多个知识点，如果都放在题中就会很多冗余】

review_steps 和 reviews 是什么关系？为什么不能合成一张表？ 【多对一的关系，因为要对每步进行判断】

如果你要查"数学学科中，知识点覆盖这个维度最常出错"， 你应该查哪几张表？（提示：至少涉及 3 张表） 【 错题，知识点，reviews】





作业二：API 设计练习

现在系统还缺一个"自由提问"的功能——学生复习卡住了，
不想看系统追问，想自己主动问一个问题。

请设计这个 API：

前端发送什么？

【发送:当前的问题】


后端返回什么？题示，这一步用到的知识点或技巧

【】




作业三：准备环境

在开始编码前，请在 PyCharm 里创建一个新项目：


打开 PyCharm → New Project

Location 选：D:\错题项目\services

勾选"Create a main.py welcome script"

Interpreter 选 "New virtual environment"

Create



环境好了,你看看"。
GReader-Archive
===============

Download all article archives from a Google Reader account.

Simple usage:   
Download code and run run.py.

For a detailed documentation (Chinese), visit http://live.aulddays.com/tech/13/google-reader-archive-download.htm

Coming soon:   
Utilities to manage downloaded files, ie, view in browser and/or export to other software like Evernote.   
下一步开发计划：已下载数据的查看、导入工具

History
-------

* Jun 03, 2013   
First version

* Jun 15, 2013   
Add 2-step verification notification

* Jun 24, 2013 
    1. Handle more http errors
    2. After all data is finished, users may delete one/all feed directory(s) in the `data` directory to download them again. (下载完成后，如果想重新下载部分或全部订阅，删除 `data` 目录下订阅对应的子目录再重新运行即可)

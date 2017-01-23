fixresources
============

Introduction
------------
`fixresources` was created to help resolve resource identifiers in disassembled Android application files (smali files).  For more information on this topic, check out my [blog](http://blog.thecobraden.com/2013/04/fixing-resource-identifiers-in.html).

Usage
-----
`fixresources` is meant to be used as a `dtf` module. After disassembling a application, you can use it as follows to enrich your smali code:

```bash
dtf fixresources path/to/app_root
```

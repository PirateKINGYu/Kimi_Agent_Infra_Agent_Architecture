#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""启动后端服务器"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

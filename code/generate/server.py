#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import errno
import logging
import datetime
from hashlib import sha1

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options



define("port", default=8000, help="Run on the given port", type=int)
define("data", default=None, help="Path to save data.", type=unicode)



def hash_hex(*args):
    h = sha1()
    for arg in args:
        h.update(arg)
    return h.hexdigest()



class Application(tornado.web.Application):
    name = u"server"
    title = u"Dotmap generate server"

    def __init__(self):
        handlers = [
            (r"/", RedirectHandler),
            (r"/save", SaveHandler),
            (r'/(.*)', tornado.web.StaticFileHandler, {'path': "."}),
            ]

        self.data_path = options.data

        assert os.path.isdir(self.data_path)

        settings = {
            }

        tornado.web.Application.__init__(self, handlers, **settings)

        sys.stdout.write(u"""%s is running.
  Address:   http://localhost:%d
""" % (
                self.title,
                options.port,
                ))
        sys.stdout.flush()



class RedirectHandler(tornado.web.RequestHandler): 
    def get(self):
        print "redirect"
        self.redirect("index.html")



class SaveHandler(tornado.web.RequestHandler):
    def post(self):
        
        key = hash_hex(self.request.body)
        data = json.loads(self.request.body)
        path = os.path.join(self.application.data_path, key + ".json")
        
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)
        print "Saved: %s" % path

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps({"path": path}))
        self.finish()
        return




def main():
    tornado.options.parse_command_line()
    
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()



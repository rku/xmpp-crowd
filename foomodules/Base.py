import shlex
import argparse

class ArgumentHelpPrinted(Exception):
    pass

class MessageHandler(object):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xmpp = None

    @property
    def XMPP(self):
        return self.xmpp

    @XMPP.setter
    def XMPP(self, value):
        self.xmpp = value

    def reply(self, origMsg, body, overrideMType=None, overrideTo=None):
        mtype = overrideMType or origMsg["type"]
        mto = overrideTo or origMsg["from"]
        if mtype == "groupchat":
            if not overrideTo:
                mto = origMsg["from"].bare
        self.xmpp.send_message(mtype=mtype, mbody=body, mto=mto)

class PrefixListener(MessageHandler):
    def __init__(self, prefix):
        super().__init__()
        self.prefix = prefix

    def _prefix_matched(self, msg, contents, errorSink=None):
        pass

    def __call__(self, msg, errorSink=None):
        contents = msg["body"]
        if not contents.startswith(self.prefix):
            return
        self._prefix_matched(msg, contents[len(self.prefix):], errorSink=errorSink)

class ArgumentParser(argparse.ArgumentParser):
    def parse_args(self, reply_method, args):
        self.reply = reply_method
        return super().parse_args(args)

    def print_help(self):
        h = self.format_help()
        self.reply(h)
        raise ArgumentHelpPrinted()

    def error(self, message):
        raise ValueError(message)

    def exit(self):
        pass

class ArgparseCommand(MessageHandler):
    def __init__(self, command_name, **kwargs):
        super().__init__()
        self.argparse = ArgumentParser(prog=command_name, **kwargs)

    def _error(self, msg, err_str):
        self.reply(msg, err_str)

    def __call__(self, msg, arguments, errorSink=None):
        args = shlex.split(arguments)
        try:
            args = self.argparse.parse_args(lambda x: self.reply(msg, x, overrideMType="chat"), args)
        except ArgumentHelpPrinted:
            return
        except ValueError as err:
            self._error(msg, str(err))
            return
        self._call(msg, args, errorSink=None)

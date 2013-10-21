import sys
import types
import logging
import gevent

class cleanup:
  def __init__(self,cleanup_func,**keys) :
    self.cleanup_func = cleanup_func
    self.keys = keys
    
  def __enter__(self):
    pass

  def __exit__(self,*args):
    if self.cleanup_func is not None:
      logging.debug("Doing cleanup")
      self.cleanup_func(**self.keys)


class error_cleanup:
  def __init__(self,*args,**keys) :
    self.error_funcs = args
    self.keys = keys

  def __enter__(self):
    pass

  def __exit__(self,*args):
    if args[0] is not None and self.error_funcs:
      logging.debug("Doing error cleanup")
      for error_func in self.error_funcs:
        try:
          error_func(**self.keys)
        except:
          logging.exception("Exception while calling cleanup on error callback %s", error_func)
          continue

class TaskException:
    def __init__(self, exception, error_string, tb):
        self.exception = exception
        self.error_string = error_string
        self.tb = tb

class wrap_errors(object):
    def __init__(self, func):
        """Make a new function from `func', such that it catches all exceptions
        and return it as a TaskException object
        """
        self.func = func

    def __call__(self, *args, **kwargs):
        func = self.func
        try:
            return func(*args, **kwargs)
        except:
            sys.excepthook(*sys.exc_info())
            return TaskException(*sys.exc_info())

    def __str__(self):
        return str(self.func)

    def __repr__(self):
        return repr(self.func)

    def __getattr__(self, item):
        return getattr(self.func, item)

def task(func):
    def start_task(*args, **kwargs):
        if args and type(args[0]) == types.InstanceType:
          logging.debug("Starting %s%s", func.__name__, args[1:])
        else:
          logging.debug("Starting %s%s", func.__name__, args)

        try:
          wait = kwargs["wait"]
        except KeyError:
          wait = True
        else:
          del kwargs["wait"]
        try:
          timeout = kwargs["timeout"]
        except KeyError:
          timeout = None 
        else:
          del kwargs["timeout"]

        try:
            t = gevent.spawn(wrap_errors(func), *args, **kwargs)
               
            if wait:
                ret = t.get(timeout = timeout)
                if isinstance(ret, TaskException):
                  sys.excepthook(ret.exception, ret.error_string, ret.tb)
                  raise ret.exception, ret.error_string
                else:
                  return ret
            else:           
                t._get = t.get
                def special_get(self, *args, **kwargs):
                  ret = self._get(*args, **kwargs)
                  if isinstance(ret, TaskException):
                    sys.excepthook(ret.exception, ret.error_string, ret.tb)
                    raise ret.exception, ret.error_string
                  else:
                    return ret
                setattr(t, "get", types.MethodType(special_get, t)) 
                
                return t
        except:
            t.kill()
            raise
          
    return start_task

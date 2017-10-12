import time


def restart(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                func(*args, **kwargs)
            except Exception as err:
                print(err, type(err))
                time.sleep(1)

    return wrapper


def restart_on(exclist):

    def outer(func):
        def inner(*args, **kwargs):
            while True:
                try:
                    func(*args, **kwargs)
                except exclist:
                    time.sleep(1)

        return inner

    return outer

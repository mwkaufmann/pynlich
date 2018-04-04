from pynlich import Component, DIV, Router


class SimplePage(Component):

    def init(self):
        console.log("site has been loaded")

    def html(self):
        test_div = DIV("this is the example page.")
        return test_div


def init():
    # register pages with the router
    Router.register("/", SimplePage)

    # start the application with the Overview Route
    Router.init("/")

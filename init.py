from pynlich import Component, DIV, Router


class SimplePage(Component):

    def init(self):
        console.log("site has been loaded")

    def html(self):
        return DIV("this is the example page.")


def init():
    # register pages with the router
    Router.register("/", SimplePage)

    # start the application with the Overview Route
    Router.init("/")

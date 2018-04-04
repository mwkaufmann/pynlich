from pynlich import Component, DIV, Router, BUTTON


class SimplePage(Component):

    def init(self):
        self.counter = 0

    def increase_counter(self):
        self.counter += 1
        self.update()

    def html(self):
        return DIV(
            f"This is the pynlich sample page: You have clicked the button {self.counter} times",
            BUTTON("click me").bind("click", self.increase_counter),
            style=dict(
                display="flex",
                flexDirection="column",
                justifyContent="center",
                alignItems="center",
                width="100%",
                height="100%"
            )
        )


def init():
    # register pages with the router
    Router.register("/", SimplePage)

    # start the application with the Overview Route
    Router.init("/")

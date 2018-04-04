
__pragma__('alias', 'jq', '$')
__pragma__('kwargs')

################################################################################

# Pynlich!
# u r welcome! :)
# V 0.2
# Mario Kaufmann, Phillipp Stengel, December 2017

################################################################################

MOUNTS = []


class Signal(object):
    """ signals can be used to send events between unrelated components """
    signals = []

    @classmethod
    def connect(cls, signal_name, cb):

        # check if the signal has already been registered
        signals_to_remove = []
        for s in cls.signals:
            # to string seems to be the only viable solution to check if the callbacks are equal
            if s["signal_name"] is signal_name and s["callback"].toString() is cb.toString():
                signals_to_remove.append(s)

        # remove already registered signals
        for s in signals_to_remove:
            cls.signals.remove(s)

        # finally append our original signal
        cls.signals.append(dict(signal_name=signal_name, callback=cb))

    @classmethod
    def emit(cls, signal_name, data=None):
        for event in cls.signals:
            if event["signal_name"] is signal_name:
                event["callback"](data)


class Event:
    def __init__(self, event_name, callback, *args):
        self.event_name = event_name
        self.callback = callback
        self.args = args


# HELPER functions

def camel_to_snake(s):
    """ used for converting CSS Attributes from Python style to CSS style """
    buff, l = '', []
    for ltr in s:
        if ltr.isupper():
            if buff:
                l.append(buff)
                buff = ''
        buff += ltr
    l.append(buff)
    return '-'.join(l).lower()


class Router(object):
    routes = {}
    timeouts = []
    intervals = []
    active_route = None

    @classmethod
    def replace(cls, target, page):
        replacement = page.render()
        target.parentNode.replaceChild(replacement, target)

    @classmethod
    def load(cls, route, *args, pushState=True, container="page", use_history=True):
        route = Router.remove_parameters(route)
        page = DIV(id=container)

        # check if route exists
        if not cls.routes[route]:
            print("route das not exist")
            return

        # at this point, we know that the route exists
        # so we can cancel all existing timeouts and intervals on this page
        Router.cancel_timeouts_and_intervals()

        if pushState:
            history.pushState(None, "", route)

        else:
            history.replaceState(None, "", route)

        # finally replace the old content with the new one
        chosen_page = cls.routes[route]()
        # chosen_page.attr(received_data=args)
        # chosen_route.data_from_last_route = args
        page.children.append(chosen_page)
        cls.active_route = route

        # jq("#" + container).replaceWith(page.render())
        old_element = document.getElementById(container)
        document.getElementById(container).replaceWith(page.render())
        old_element.remove()

        # after DOM has been fully loaded we can call all mounted functions
        cls.call_mounts()

    @classmethod
    def call_mounts(cls):
        global MOUNTS
        for m in MOUNTS:
            m['cb'](m['element'])
        MOUNTS = []

    @classmethod
    def register(cls, route, content):
        cls.routes[route] = content

    @classmethod
    def set_timeout(cls, callback, time):
        Router.timeouts.append(setTimeout(callback, time))

    @classmethod
    def set_interval(cls, callback, time):
        Router.intervals.append(setInterval(callback, time))

    @classmethod
    def cancel_timeouts_and_intervals(cls):
        for timeout in Router.timeouts:
            clearTimeout(timeout)

        for interval in Router.intervals:
            clearInterval(interval)

        Router.timeouts = []
        Router.intervals = []

    @classmethod
    def init(cls, route):
        # todo: check if init and load can be merged

        def hash_changed():
            Router.load(window.location.hash, pushState=False)

        # if user changes hash from hand, also load the new content
        jq(window).on("hashchange", lambda: hash_changed())

        # check if hash already exists
        if window.location.hash:
            Router.load(window.location.hash)
        else:
            Router.load(route, pushState=False)

    @classmethod
    def remove_parameters(cls, route):
        split_hash = route.split('?')
        return split_hash[0]


class Component:
    def __init__(self, *children, **kwargs):

        self.children = list(children)
        self._events = []
        self._mounts = []

        # add style list, if styles have been given as key word argument

        if "style" in kwargs:
            self.styles = kwargs.get("style")
            del kwargs["style"]
        else:
            self.styles = {}

        # copy relevant information to instance attributes

        self._args = kwargs
        self._name = self.__class__.__name__

        # add user defined content

        if self.init:
            self.init()


    def attr(self, **kwargs):
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])
        return self

    """
    def init(self, **args):
        for k, v in args.items():
            self.k = v
    """

    def render(self):

        if self.children is js_undefined:
            # return P("ERROR")
            return None

        # decide if we should render the children or the html elements
        # self._children = []
        elements_to_append = []
        if self.html:
            elements_to_append.append(self.html())
        else:
            elements_to_append.extend(self.children)

        # flatten and clean list
        flattened = []
        for e in elements_to_append:
            if e is not js_undefined:
                if type(e) is list or type(e) is tuple:
                    flattened.extend(e)
                else:
                    flattened.append(e)

        # create DOM Element
        fragment = document.createDocumentFragment()
        element = document.createElement(self._name)

        # apply css styles

        for k, v in self.styles.items():
            element.style[k] = v

        # add other attributes

        for k, v in self._args.items():
            # only add the attribute if it has an associated value
            if v:
                element.setAttribute(camel_to_snake(k), v)

        # attach event listeners

        for event in self._events:
            # element.addEventListener(event.event_name, lambda x: event.callback(x, *event.args))
            element.addEventListener(event.event_name, event.callback)

        # add mounts to global mount object. We will call them later, after the page has been fully loaded

        global MOUNTS
        for mount in self._mounts:
            MOUNTS.append(dict(cb=mount, element=element))

        # render all children
        for child in flattened:
            if not child:
                continue


            if type(child) is str or type(child) is int:
                fragment.appendChild(document.createTextNode(str(child)))
            else:
                # TODO: child render could still fail, if already rendered element has been passed
                # TODO: child render can feail here, if a list was passed
                if type(child) is list:
                    if DEBUG: console.log('warning, list passed to render func')
                    child = child[0]
                c = child.render()
                if c:
                    fragment.appendChild(c)

        element.appendChild(fragment)
        self._cache = element
        return element

    def update(self):
        # console.log("replacing")
        # console.log(self._cache)
        # console.log("with")
        # console.log(self.render())

        old_element = self._cache
        if old_element:
            old_element.parentNode.replaceChild(self.render(), old_element)
            old_element.remove()
            Router.call_mounts()

    def remove_class(self, class_name):
        jq(self._cache).removeClass(class_name)

    def add_class(self, class_name):
        jq(self._cache).addClass(class_name)

    def find(self, selector):
        return jq(self._cache).find(selector)

    def bind(self, event_name, callback, *args):
        self._events.append(Event(event_name, callback, *args))
        return self

    def mounted(self, cb):
        # register mount for later processing
        self._mounts.append(cb)
        return self


    # def _save_to_html(self):
    #     """ experimental saving the pynlich generated html to disk """
    #     htmlContent = self._cache
    #     bl = __new__(Blob([htmlContent.innerHTML], {"type": "text/html"}))
    #     a = document.createElement("a")
    #     a.href = URL.createObjectURL(bl)
    #     a.download = "pynlich_generated.html"
    #     a.hidden = True
    #     document.body.appendChild(a)
    #     a.innerHTML = "something random"
    #     a.click()


class A(Component):
    pass


class ABBR(Component):
    pass


class ACRONYM(Component):
    pass


class ADDRESS(Component):
    pass


class APPLET(Component):
    pass


class AREA(Component):
    pass


class B(Component):
    pass


class BASE(Component):
    pass


class BASEFONT(Component):
    pass


class BDO(Component):
    pass


class BIG(Component):
    pass


class BLOCKQUOTE(Component):
    pass


class BODY(Component):
    pass


class BR(Component):
    pass


class BUTTON(Component):
    pass


class CAPTION(Component):
    pass


class CENTER(Component):
    pass


class CITE(Component):
    pass


class CODE(Component):
    pass


class COL(Component):
    pass


class COLGROUP(Component):
    pass


class DD(Component):
    pass


class DEL(Component):
    pass


class DFN(Component):
    pass


class DIR(Component):
    pass


class DIV(Component):
    pass


class DL(Component):
    pass


class DT(Component):
    pass


class EM(Component):
    pass


class FIELDSET(Component):
    pass


class FONT(Component):
    pass


class FORM(Component):
    pass


class FRAME(Component):
    pass


class FRAMESET(Component):
    pass


class H1(Component):
    pass


class H2(Component):
    pass


class H3(Component):
    pass


class H4(Component):
    pass


class H5(Component):
    pass


class H6(Component):
    pass


class HEAD(Component):
    pass


class HR(Component):
    pass


class HTML(Component):
    pass


class I(Component):
    pass


class IFRAME(Component):
    pass


class IMG(Component):
    pass


class INPUT(Component):
    pass


class INS(Component):
    pass


class ISINDEX(Component):
    pass


class KBD(Component):
    pass


class LABEL(Component):
    pass


class LEGEND(Component):
    pass


class LI(Component):
    pass


class LINK(Component):
    pass


class MAP(Component):
    pass


class MENU(Component):
    pass


class META(Component):
    pass


class NOFRAMES(Component):
    pass


class NOSCRIPT(Component):
    pass


class OBJECT(Component):
    pass


class OL(Component):
    pass


class OPTGROUP(Component):
    pass


class OPTION(Component):
    pass


class P(Component):
    pass


class PARAM(Component):
    pass


class PRE(Component):
    pass


class Q(Component):
    pass


class S(Component):
    pass


class SAMP(Component):
    pass


class SCRIPT(Component):
    pass


class SELECT(Component):
    pass


class SMALL(Component):
    pass


class SPAN(Component):
    pass


class STRIKE(Component):
    pass


class STRONG(Component):
    pass


class STYLE(Component):
    pass


class SUB(Component):
    pass


class SUP(Component):
    pass


class SVG(Component):
    pass


class RECT(Component):
    pass


class TABLE(Component):
    pass


class TBODY(Component):
    pass


class TD(Component):
    pass


class TEXTAREA(Component):
    pass


class TFOOT(Component):
    pass


class TH(Component):
    pass


class THEAD(Component):
    pass


class TITLE(Component):
    pass


class TR(Component):
    pass


class TT(Component):
    pass


class U(Component):
    pass


class UL(Component):
    pass


class VAR(Component):
    pass


class ARTICLE(Component):
    pass


class ASIDE(Component):
    pass


class AUDIO(Component):
    pass


class BDI(Component):
    pass


class CANVAS(Component):
    pass


class COMMAND(Component):
    pass


class DATA(Component):
    pass


class DATALIST(Component):
    pass


class EMBED(Component):
    pass


class FIGCAPTION(Component):
    pass


class FIGURE(Component):
    pass


class FOOTER(Component):
    pass


class HEADER(Component):
    pass


class KEYGEN(Component):
    pass


class MAIN(Component):
    pass


class MARK(Component):
    pass


class MATH(Component):
    pass


class METER(Component):
    pass


class NAV(Component):
    pass


class OUTPUT(Component):
    pass


class PROGRESS(Component):
    pass


class RB(Component):
    pass


class RP(Component):
    pass


class RT(Component):
    pass


class RTC(Component):
    pass


class RUBY(Component):
    pass


class SECTION(Component):
    pass


class SOURCE(Component):
    pass


class TEMPLATE(Component):
    pass


class TIME(Component):
    pass


class TRACK(Component):
    pass


class VIDEO(Component):
    pass


class WBR(Component):
    pass


class DETAILS(Component):
    pass


class DIALOG(Component):
    pass


class MENUITEM(Component):
    pass


class PICTURE(Component):
    pass


class SUMMARY(Component):
    pass


__pragma__('nokwargs')

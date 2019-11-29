"""Pygments related rendering
"""


import urwid
import pygments
from pygments.formatter import Formatter
import urwid


import lookatme.config as config


def render_text(text, lang="text", style_name=None, plain=False):
    """Render the provided text with the pygments renderer
    """
    if style_name is None:
        style_name = config.STYLE["style"]
    style = pygments.styles.get_style_by_name(style_name)
    style_bg = UrwidFormatter.findclosest(style.background_color.replace("#", ""))

    lexer = pygments.lexers.get_lexer_by_name(lang)
    formatter = UrwidFormatter(
        style=style_name,
        usebg=(style_bg is not None),
    )
    code_tokens = lexer.get_tokens(text)

    markup = []
    for x in formatter.formatgenerator(code_tokens):
        if style_bg:
            x[0].background = style_bg
        markup.append(x)

    if markup[-1][1] == "\n":
        markup = markup[:-1]

    if markup[-1][1].endswith("\n"):
        markup[-1] = (markup[-1][0], markup[-1][1][:-1])

    if plain:
        return markup
    else:
        return urwid.AttrMap(urwid.Text(markup), urwid.AttrSpec("default", style_bg))


class UrwidFormatter(Formatter):
    """Formatter that returns [(text,attrspec), ...],
    where text is a piece of text, and attrspec is an urwid.AttrSpec"""
    def __init__(self, **options):
        """Extra arguments:
        
        usebold: if false, bold will be ignored and always off
                default: True
        usebg: if false, background color will always be 'default'
                default: True
        colors: number of colors to use (16, 88, or 256)
                default: 256"""
        self.usebold = options.get('usebold',True)
        self.usebg = options.get('usebg', True)
        colors = options.get('colors', 256)
        self.style_attrs = {}
        Formatter.__init__(self, **options)
        
    @property
    def style(self):
        return self._style
    
    @style.setter
    def style(self, newstyle):
        self._style = newstyle
        self._setup_styles()
        
    @staticmethod
    def _distance(col1, col2):
        r1, g1, b1 = col1
        r2, g2, b2 = col2
        
        rd = r1 - r2
        gd = g1 - g2
        bd = b1 - b2
        
        return rd*rd + gd*gd + bd*bd
    
    @classmethod
    def findclosest(cls, colstr, colors=256):
        """Takes a hex string and finds the nearest color to it.
        
        Returns a string urwid will recognize."""
        
        rgb = int(colstr, 16)
        r = (rgb >> 16) & 0xff
        g = (rgb >> 8) & 0xff
        b = rgb & 0xff
        
        dist = 257 * 257 * 3
        bestcol = urwid.AttrSpec('h0','default')
        
        for i in range(colors):
            curcol = urwid.AttrSpec('h%d' % i,'default', colors=colors)
            currgb = curcol.get_rgb_values()[:3]
            curdist = cls._distance((r,g,b), currgb)
            if curdist < dist:
                dist = curdist
                bestcol = curcol
        
        return bestcol.foreground
    
    def findclosestattr(self, fgcolstr=None, bgcolstr=None, othersettings='', colors = 256):
        """Takes two hex colstring (e.g. 'ff00dd') and returns the 
        nearest urwid style."""
        fg = bg = 'default'
        if fgcolstr:
            fg = self.findclosest(fgcolstr, colors)
        if bgcolstr:
            bg = self.findclosest(bgcolstr, colors)
        if othersettings:
            fg = fg + ',' + othersettings
        return urwid.AttrSpec(fg, bg, colors)
    
    def _setup_styles(self, colors = 256):
        """Fills self.style_attrs with urwid.AttrSpec attributes 
        corresponding to the closest equivalents to the given style."""
        for ttype, ndef in self.style:
            fgcolstr = bgcolstr = None
            othersettings = ''
            if ndef['color']:
                fgcolstr = ndef['color']
            if self.usebg and ndef['bgcolor']:
                bgcolstr = ndef['bgcolor']
            if self.usebold and ndef['bold']:
                othersettings = 'bold'
            self.style_attrs[str(ttype)] = self.findclosestattr(
                fgcolstr, bgcolstr, othersettings, colors)
        
    def formatgenerator(self, tokensource):
        """Takes a token source, and generates 
        (tokenstring, urwid.AttrSpec) pairs"""
        for (ttype, tstring) in tokensource:
            while str(ttype) not in self.style_attrs:
                ttype = ttype[:-1]

            attr = self.style_attrs[str(ttype)]
            yield attr, tstring
    
    def format(self, tokensource, outfile):
        for (attr, tstring) in self.formatgenerator(tokensource):
            outfile.write(attr, tstring)

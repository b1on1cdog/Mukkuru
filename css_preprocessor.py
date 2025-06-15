''' Preprocess CSS for logic purposes '''
from pathlib import Path
from io import BytesIO
import re

class CssPreprocessor:
    """ Main class """
    def __init__(self, path):
        ''' Receives the CSS string and returns CSS buffer'''
        self.prefix = "Mukkuru::"
        self.functions = ["BackgroundLinearGradientRotation"]
        if Path(path).is_file():
            with open(path, 'r', encoding='utf-8') as css_file:
                self.css = css_file.read()
                print(f"Processing CSS {path}...")
        else:
            self.css = None
            print(f"Unable to process CSS {path}...")
    def process(self):
        ''' Replace sytax '''
        for function in self.functions:
            prefix = self.prefix + function + "("
            pattern = re.compile(rf'{re.escape(prefix)}.*?\);')
            for match in pattern.findall(self.css):
                command = match.replace(prefix, "")
                command = command.replace(");", "")
                args = command.split("$#")
                if function == "BackgroundLinearGradientRotation":
                    rotation = float(args[0])
                    interval = float(args[1])
                    parameter = args[2]
                    replacement = self.lenion_one(rotation, interval, parameter)
                    print(f"lenion_one{replacement}")
                    self.css = self.css.replace(match, replacement)

    def lenion_one(self, rotation, interval, parameter):
        ''' Produce snippet for  BackgroundLinearGradientRotation'''
        n = 0.0
        content = ""
        line = '''
    %i% {
        background: linear-gradient(%ndeg,%p);
    }
'''
        while n <= 100.0:
            s = "{:.1f}".format(n)
            c = line.replace('%i', s)
            c = c.replace('%n', str( int(n*rotation) ) )
            c = c.replace('%p', parameter)
            content += "\n"+ c
            n += interval
        return content

    def data(self):
        """ Returns css as bytes """
        buffer = BytesIO()
        buffer.write(str.encode(self.css))
        buffer.seek(0)
        return buffer

    def text(self):
        ''' Returns css as string'''
        return self.css

# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Preprocess CSS for logic purposes '''
from pathlib import Path
from io import BytesIO
import re

class CssPreprocessor:
    """ Main class """
    def __init__(self, path = None, data = None):
        ''' Receives the CSS string and returns CSS buffer'''
        self.prefix = "/*Mukkuru::"
        self.suffix = ");*/"
        self.functions = ["BackgroundLinearGradientRotation"]
        if path is not None and Path(path).is_file():
            with open(path, 'r', encoding='utf-8') as css_file:
                self.css = css_file.read()
                print(f"Processing CSS {path}...")
        elif data is not None:
            self.css = data
            print("Processing CSS data...")
        else:
            self.css = None
            print(f"Unable to process CSS {path}...")
    def process(self):
        ''' Replace sytax '''
        for function in self.functions:
            prefix = self.prefix + function + "("
            pattern = re.compile(rf'{re.escape(prefix)}.*?{re.escape(self.suffix)}')
            for match in pattern.findall(self.css):
                #print(f"m: {match}")
                command = match.replace(prefix, "")
                command = command.replace(self.suffix, "")
                args = command.split("$#")
                if function == "BackgroundLinearGradientRotation":
                    interval = float(args[0])
                    parameter = args[1]
                    replacement = self.lenion_one(interval, parameter)
                    #print(f"lenion_one{replacement}")
                    self.css = self.css.replace(match, replacement)

    def lenion_one(self, interval, parameter):
        ''' Produce snippet for  BackgroundLinearGradientRotation'''
        n = 0.1
        content = ""
        line = '''
    %i% {
        background: linear-gradient(%ndeg,%p);
    }
'''
        while n <= 100.0:
            s = f"{n:.1f}"
            c = line.replace('%i', s)
            c = c.replace('%n', f"{( (n/100)*357 ):.2f}")
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
